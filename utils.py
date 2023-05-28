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

    
def check_whisper():
    model_dir = './models/base.pt'
    if os.path.isfile(model_dir):
        logging.info(f'Whisper base model exists, reusing.')
    else:
        os.makedirs('./models/')
        logging.info(f'Downloading Whisper base model to {dir}.')
    return load_whisper(dir=model_dir)

def capture_microphone():
    audio = RecordThread.RecordThread()
    audio.start()
    return audio

def generate_waveform(nparray):
    # nparray should be from audio.get_nparray()
    fig = plt.figure()
    s = fig.add_subplot()
    s.plot(nparray)
    fig.savefig('fig.jpg')
    return

def downsample(nparray):
    ratio = 16000/48000
    converter = 'sinc_fastest'
    return samplerate.resample(input_data=nparray, ratio=ratio, converter_type=converter)
