import pyaudio

audio = pyaudio.PyAudio()

default_api_info = list(audio.get_default_host_api_info().values()) # ['index', 'structVersion', 'type', 'name', 'deviceCount', 'defaultInputDevice', 'defaultOutputDevice']
print(audio.get_device_info_by_host_api_device_index(default_api_info[0], default_api_info[5]))
# wASABI: {'index': 2, 'structVersion': 1, 'type': 13, 'name': 'Windows WASAPI', 'deviceCount': 6, 'defaultInputDevice': 20, 'defaultOutputDevice': 18}
# WASABI default output: {'index': 18, 'structVersion': 2, 'name': '耳機 (Arctis Pro Wireless Game)', 'hostApi': 2, 'maxInputChannels': 0, 'maxOutputChannels': 2, 'defaultLowInputLatency': 0.0, 'defaultLowOutputLatency': 0.003, 'defaultHighInputLatency': 0.0, 'defaultHighOutputLatency': 0.01, 'defaultSampleRate': 48000.0}

for x in range(audio.get_device_count()):
     print(audio.get_device_info_by_index(x))
audio.terminate()