import os
import logging
import torch
import whisper
import matplotlib.pyplot as plt
import samplerate

import RecordThread

def check_torch():
    if torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    logging.info(f'Torch is currently running on {device.type.upper()}.')
    return

def load_whisper(dir):
    whisper_model = whisper.load_model('base', download_root='./models/')
    return whisper_model

    
def check_whisper(model_size: str):
    model_dir = f'./models/{model_size}.pt'
    if os.path.isfile(model_dir):
        logging.info(f'Whisper {model_size} model exists, reusing.')
    else:
        os.makedirs('./models/')
        logging.info(f'Downloading Whisper base model to {dir}.')
    return load_whisper(dir=model_dir)

def capture_microphone(queue):
    audio = RecordThread.RecordThread(queue)
    logging.info("Starting microphone capture.")
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
    s.hlines(volThreshold*-1, xmin, xmax, colors="red")
    s.set_xlabel('Samples')
    fig.savefig('fig.jpg')
    plt.close('all')
    return

def downsample(nparray):
    ratio = 16000/48000
    converter = 'sinc_fastest'
    return samplerate.resample(input_data=nparray, ratio=ratio, converter_type=converter)
