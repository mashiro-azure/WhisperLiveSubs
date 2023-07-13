import os

os.add_dll_directory('C:/Users/henry/source/repos/whisper-nllb/')

import audioop
from queue import Queue
import threading

import numpy as np
import pyaudio


class RecordThread(threading.Thread):
    def __init__(self, queue: Queue):
        threading.Thread.__init__(self)
        self.audio = pyaudio.PyAudio()
        self.default_api_info = list(self.audio.get_default_host_api_info().values())
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 48000
        self.chunk = 1024
        # self.device = self.default_api_info[5]
        self.device = 16
        self.record = True
        self.frames = b''
        self.chunk_data = ''
        self.volThreshold = 0
        # self.voiceActivityLengthMS = 200 # how long should a sentence be
        # self.voiceActivitySamples = self.rate*(self.voiceActivityLengthMS/1000)
        self.voiceTimeoutMS = 1000
        self.voiceTimeoutSamples = self.rate*(self.voiceTimeoutMS/1000)
        self.eventQueue = queue

    def set_volThreshold(self, volThreshold: int):
        self.volThreshold = volThreshold

    # def set_voiceActivityLengthMS(self, volThresholdLengthMS: int):
    #     self.voiceActivityLengthMS = volThresholdLengthMS
    #     self.voiceActivitySamples = self.rate*(self.voiceActivityLengthMS/1000)

    def set_voiceTimeoutMS(self, voiceTimeoutMS: int):
        self.voiceTimeoutMS = voiceTimeoutMS
        self.voiceTimeoutSamples = self.rate*(self.voiceTimeoutMS/1000)


    def run(self):
        audio_stream = self.audio.open(format=self.format, channels=self.channels, rate=self.rate, frames_per_buffer=self.chunk, input=True, input_device_index=self.device)
        talking_samples = 0
        silent_samples = 0
        
        while self.record:
            self.chunk_data = audio_stream.read(self.chunk)
            self.chunk_rms = audioop.rms(self.chunk_data, 2)
            self.frames += bytearray(self.chunk_data)
            # print(f'talking_samples:{talking_samples}, silent_samples:{silent_samples}')

            isSpeech = self.chunk_rms >= self.volThreshold # if voice volume larger than threshold
            # isSpeechLongerThanThreshold = talking_samples > self.voiceActivitySamples
            isSilenceLongerThanThreshold = silent_samples > self.voiceTimeoutSamples

            if isSpeech:
                talking_samples += self.chunk
                silent_samples = 0
            else: 
                # if voice volume lower than threshold, consider as silence
                silent_samples += self.chunk
                
            if (isSilenceLongerThanThreshold) and (talking_samples != 0) or (talking_samples >= 480000): 
                # voice detected
                print(f'speech full: talking_samples:{talking_samples}, silent_samples:{silent_samples}')
                self.eventQueue.put({'audio_buffer': 'full'})
                talking_samples = 0
                silent_samples = 0
            elif (isSilenceLongerThanThreshold) and (talking_samples == 0): 
                # audio below threshold, assume not talking, reset audio buffer and restart recording
                print(f'no speech: talking_samples:{talking_samples}, silent_samples:{silent_samples}')
                talking_samples = 0
                silent_samples = 0
                self.frames = b''
                self.chunk_data = ''
            # elif silent_samples > 480000: # silence longer than 30s
            #     print(f'silent_samples duration exceeded, dumping previous audio.')
            #     self.frames = b''
            #     silent_samples = 0

        audio_stream.stop_stream()
        audio_stream.close()
        self.audio.terminate()

    def get_nparray(self):
        self.real_audio = (np.frombuffer(self.frames, np.int16).flatten().astype(np.float32) / 32768.0)
        # clear buffer to prepare for the next loop
        self.frames = b''
        self.chunk_data = ''
        return self.real_audio

    def stop(self):
        self.record = False