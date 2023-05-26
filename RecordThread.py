import pyaudio
import threading
import numpy as np

class RecordThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.audio = pyaudio.PyAudio()
        self.default_api_info = list(self.audio.get_default_host_api_info().values())
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 48000
        self.chunk = 1024
        # self.device = self.default_api_info[5]
        self.device = 20
        self.record = True
        self.frames = b''
        self.chunk_data = ''

    def run(self):
        audio_stream = self.audio.open(format=self.format, channels=self.channels, rate=self.rate, frames_per_buffer=self.chunk, input=True, input_device_index=self.device)
        while self.record:
            self.chunk_data = audio_stream.read(self.chunk)
            self.frames += bytearray(self.chunk_data)
            self.real_audio = (np.frombuffer(self.frames, np.int16).flatten().astype(np.float32) / 32768.0)
        audio_stream.stop_stream()
        audio_stream.close()
        self.audio.terminate()

    def get_nparray(self):
        return self.real_audio

    def stop(self):
        self.record = False