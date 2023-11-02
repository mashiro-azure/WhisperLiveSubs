import logging
import os
from queue import Queue

import matplotlib.pyplot as plt
import pyaudio
import torch
import whisper
from torchaudio.transforms import Resample

from . import RecordThread

log = logging.getLogger("logger")


def check_torch(enableGPU: str):  # FP16 not supported on CPU
    if torch.cuda.is_available() and (enableGPU == "true"):
        device = torch.device("cuda")
        fp16 = True
    else:
        device = torch.device("cpu")
        fp16 = False
    torch.set_default_device(device)

    log.info(f"Torch is currently running on {device.type.upper()}.")
    return device, fp16


# def load_whisper(dir: str, device: torch.device):
#     whisper_model = whisper.load_model("base", download_root="./models/", device=device)
#     return whisper_model


def check_whisper(model_size: str, device: torch.device):
    model_root = str(os.getcwd() + os.sep + "backend" + os.sep)
    model_folderName = f"models{os.sep}"
    model_folderPath = model_root + model_folderName
    model_filePath = f"{model_root + model_folderName + model_size}.pt"
    if os.path.isfile(model_filePath):
        log.info(f"Whisper {model_size} model exists, reusing.")
    else:
        try:
            os.makedirs(f".{os.sep}backend{os.sep}{model_folderName}")
            log.info(f"Downloading Whisper {model_size} model to {model_folderPath}")
        except FileExistsError:
            log.error(f"Directory 'backend{os.sep}{model_folderName}' exists, attempting to download model.")
    return whisper.load_model(model_size, device, download_root=model_folderPath)


def capture_microphone(eventQueue: Queue, userSettings: dict):
    audio = RecordThread.RecordThread(eventQueue, userSettings)
    log.info("Starting microphone capture.")
    audio.start()
    return audio


def generate_waveform(nparray, volThreshold: float):
    # nparray should be from audio.get_nparray()
    fig = plt.figure()
    s = fig.add_subplot()
    s.plot(nparray)
    ax = fig.gca()
    xmin, xmax, _, _ = ax.axis()
    s.hlines(volThreshold, xmin, xmax, colors="red")
    s.hlines(volThreshold * -1, xmin, xmax, colors="red")
    s.set_xlabel("Samples")
    fig.savefig("fig.jpg")
    plt.close("all")
    return


def downsample(audioTensor: torch.Tensor, input_rate: int):
    orig_freq = input_rate
    new_freq = 16000
    transform = Resample(orig_freq=orig_freq, new_freq=new_freq)
    audioTensor = transform(audioTensor)
    return audioTensor


def refresh_audio_API_list():
    """Gets audio device information for frontend

    Arguments: Requires none

    Returns:
    dict: {"apiCount": int, "apiType": [int], "apiName": [str]}
    """
    pa = pyaudio.PyAudio()
    # Host API
    apiCount = pa.get_host_api_count()
    apiType, apiName = [], []
    for i in range(apiCount):
        apiInfo = pa.get_host_api_info_by_index(i)
        apiType.append(apiInfo["type"])
        apiName.append(apiInfo["name"])
    pa.terminate()

    returnData = {"apiCount": apiCount, "apiType": apiType, "apiName": apiName}
    return returnData


def refresh_audio_device_list(apiType: int):
    """Gets audio device informaion from specified API

    Arguments: PyAudio's apiType: int

    Returns:
    dict: {"deviceList": dict}
    "deviceList": lists of audio device controlled by the specified API.
    """
    pa = pyaudio.PyAudio()
    apiInfo = pa.get_host_api_info_by_type(apiType)
    deviceCount = int(apiInfo["deviceCount"])
    apiIndex = int(apiInfo["index"])
    deviceList = []
    for i in range(deviceCount):
        deviceInfo = pa.get_device_info_by_host_api_device_index(apiIndex, i)
        if int(deviceInfo["maxInputChannels"]) >= 1:
            deviceList.append(deviceInfo)
    pa.terminate()

    returnData = {"deviceList": deviceList}
    return returnData
