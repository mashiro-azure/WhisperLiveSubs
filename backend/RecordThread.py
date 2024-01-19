import audioop
import logging
import os
import threading
from queue import Queue

import numpy as np
import torch
from torchaudio.transforms import Resample

log = logging.getLogger("logger")
if os.name == "nt":
    log.info(
        "Windows detected. If WASAPI loopback devices are required, please compile PortAudio & PyAudio manually, and place portaudio_x64.dll to PyAudio's site-packages folder."  # noqa:E501
    )
import pyaudio  # noqa:E402


class RecordThread(threading.Thread):
    def __init__(self, queue: Queue, userSettings: dict):
        threading.Thread.__init__(self)
        self.name = "Mic Recording"
        self.daemon = True
        self.audio = pyaudio.PyAudio()
        # self.default_api_info = list(self.audio.get_default_host_api_info().values())
        self.format = pyaudio.paInt16
        self.channels = userSettings["AudioChannel"]
        self.rate = userSettings["AudioSampleRate"]
        self.chunkSize = 1024
        # self.device = self.default_api_info[5]
        self.device = userSettings["InputDevice"]
        self.record = True
        self.frames = bytearray()
        self.chunk_data = ""
        self.volThreshold = 0
        # self.voiceActivityLengthMS = 200 # how long should a sentence be
        # self.voiceActivitySamples = self.rate*(self.voiceActivityLengthMS/1000)
        self.voiceTimeoutMS = 1000
        self.voiceTimeoutSamples = self.rate * (self.voiceTimeoutMS / 1000)
        self.eventQueue = queue

    def set_volThreshold(self, volThreshold: int):
        self.volThreshold = volThreshold

    # def set_voiceActivityLengthMS(self, volThresholdLengthMS: int):
    #     self.voiceActivityLengthMS = volThresholdLengthMS
    #     self.voiceActivitySamples = self.rate*(self.voiceActivityLengthMS/1000)

    def set_voiceTimeoutMS(self, voiceTimeoutMS: int):
        self.voiceTimeoutMS = voiceTimeoutMS
        self.voiceTimeoutSamples = self.rate * (self.voiceTimeoutMS / 1000)

    def run(self):
        audio_stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            frames_per_buffer=self.chunkSize,
            input=True,
            input_device_index=self.device,
        )
        talking_samples = 0
        silent_samples = 0

        while self.record:
            self.chunk_data = audio_stream.read(self.chunkSize)
            self.chunk_rms = audioop.rms(self.chunk_data, 2)
            self.frames += bytearray(self.chunk_data)
            # print(f'talking_samples:{talking_samples}, silent_samples:{silent_samples}')

            isSpeech = self.chunk_rms >= self.volThreshold  # if voice volume larger than threshold
            # isSpeechLongerThanThreshold = talking_samples > self.voiceActivitySamples
            isSilenceLongerThanThreshold = silent_samples > self.voiceTimeoutSamples

            if isSpeech:
                talking_samples += self.chunkSize
                silent_samples = 0
            else:
                # if voice volume lower than threshold, consider as silence
                silent_samples += self.chunkSize

            if (isSilenceLongerThanThreshold and talking_samples != 0) or (talking_samples >= 480000):
                # voice detected
                log.debug(f"speech full: talking_samples:{talking_samples}, silent_samples:{silent_samples}")
                self.eventQueue.put({"audio_buffer": "full"})
                talking_samples = 0
                silent_samples = 0
            elif (isSilenceLongerThanThreshold) and (talking_samples == 0):
                # audio below threshold, assume not talking, reset audio buffer and restart recording
                log.debug(f"no speech: talking_samples:{talking_samples}, silent_samples:{silent_samples}")
                talking_samples = 0
                silent_samples = 0
                self.frames = b""
                self.chunk_data = ""
            # elif silent_samples > 480000: # silence longer than 30s
            #     print(f'silent_samples duration exceeded, dumping previous audio.')
            #     self.frames = b''
            #     silent_samples = 0

        audio_stream.stop_stream()
        audio_stream.close()
        self.audio.terminate()

    def get_audioTensor(self) -> torch.Tensor:
        """Downmix, downscales audio and turns it into a tensor. Performs on CPU ony."""
        audioBytes = np.frombuffer(self.frames, dtype=np.int16).flatten().astype(np.float32) / 32768.0
        if self.channels > 1:
            # Downmix
            audioTensor: torch.Tensor = downmix(audioBytes)
        elif self.channels == 1:
            audioTensor: torch.Tensor = torch.from_numpy(audioBytes)
        # downsample, this returns a 2d array
        downsampledAudioTensor = downsample(audioTensor, self.rate)
        # whisper expects a 1d array
        downsampledAudioTensor = downsampledAudioTensor.flatten()
        # clear buffer to prepare for the next loop
        self.frames = b""
        self.chunk_data = ""
        return downsampledAudioTensor

    def stop(self):
        self.record = False


def downmix(audioBytes) -> torch.Tensor:
    """Separate two channels, pyaudio spits out audio data like [LEFT,RIGHT,LEFT,RIGHT,...]"""
    audioBytes = np.reshape(audioBytes, (-1, 2))
    audioBytes = np.transpose(audioBytes)
    audioTensor: torch.Tensor = torch.from_numpy(audioBytes)
    audioTensor_mono: torch.Tensor = torch.mean(audioTensor, dim=0, keepdim=True)
    return audioTensor_mono


def downsample(audioTensor: torch.Tensor, input_rate: int) -> torch.Tensor:
    orig_freq = input_rate
    new_freq = 16000
    transform = Resample(orig_freq=orig_freq, new_freq=new_freq)
    audioTensor = transform(audioTensor)
    return audioTensor
