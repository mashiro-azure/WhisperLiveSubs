import os
os.add_dll_directory('C:/Users/henry/source/repos/whisper-nllb/')

import pyaudio

audio = pyaudio.PyAudio()

default_api_info = list(audio.get_default_host_api_info().values()) # ['index', 'structVersion', 'type', 'name', 'deviceCount', 'defaultInputDevice', 'defaultOutputDevice']
print(audio.get_device_info_by_host_api_device_index(default_api_info[0], default_api_info[5]))
# wASABI: {'index': 2, 'structVersion': 1, 'type': 13, 'name': 'Windows WASAPI', 'deviceCount': 6, 'defaultInputDevice': 20, 'defaultOutputDevice': 18}
# WASABI default output: {'index': 18, 'structVersion': 2, 'name': '耳機 (Arctis Pro Wireless Game)', 'hostApi': 2, 'maxInputChannels': 0, 'maxOutputChannels': 2, 'defaultLowInputLatency': 0.0, 'defaultLowOutputLatency': 0.003, 'defaultHighInputLatency': 0.0, 'defaultHighOutputLatency': 0.01, 'defaultSampleRate': 48000.0}

wasapi_api = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
wasapi_api_index = wasapi_api.get('index')
wasapi_api_deviceCount = wasapi_api.get('deviceCount')
for x in range(wasapi_api_deviceCount):
     print(audio.get_device_info_by_host_api_device_index(wasapi_api_index, x))
audio.terminate()