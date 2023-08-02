import logging
import os
import sys
from queue import Queue

import matplotlib.pyplot as plt
import samplerate
import torch
import whisper

import RecordThread

log = logging.getLogger("logger")


def check_torch():
    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    torch.set_default_device(device)

    log.info(f"Torch is currently running on {device.type.upper()}.")
    return device


# def load_whisper(dir: str, device: torch.device):
#     whisper_model = whisper.load_model("base", download_root="./models/", device=device)
#     return whisper_model


def check_whisper(model_size: str, device: torch.device):
    model_root = str(os.getcwd() + os.sep)
    model_folderName = f"models{os.sep}"
    model_folderPath = model_root + model_folderName
    model_filePath = f"{model_root + model_folderName + model_size}.pt"
    if os.path.isfile(model_filePath):
        log.info(f"Whisper {model_size} model exists, reusing.")
    else:
        try:
            os.makedirs(f".{os.sep}{model_folderName}")
            log.info(f"Downloading Whisper {model_size} model to {model_folderPath}.")
        except FileExistsError:
            log.error(f"Directory '{model_folderName}' exists, please remove or rename the directory.")
            sys.exit()
    return whisper.load_model(model_size, device, download_root=model_folderPath)


def capture_microphone(eventQueue: Queue):
    audio = RecordThread.RecordThread(eventQueue)
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


def downsample(nparray):
    ratio = 16000 / 48000
    converter = "sinc_fastest"
    return samplerate.resample(nparray, ratio, converter)
