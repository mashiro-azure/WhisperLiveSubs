import torch
import sys
import whisper
import logging
import numpy as np
import matplotlib.pyplot as plt

import utils
import time

def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    utils.check_torch()
    whisper_model = utils.check_whisper()

    audio = utils.capture_microphone()

    time.sleep(5)

    nparray = audio.get_nparray()
    audio.stop()
    # downsample (mandatory?)
    nparray = utils.downsample(nparray)
    ## matplotlib
    utils.generate_waveform(nparray)
    ## matplotlib

    N_SAMPLES = 16000*30
    real_audio = whisper.pad_or_trim(nparray, length=N_SAMPLES)

    mel = whisper.log_mel_spectrogram(real_audio, padding=int(N_SAMPLES - real_audio.shape[0])).to(whisper_model.device)

    options = whisper.DecodingOptions(fp16=False, language='ja')
    result = whisper.decode(whisper_model, mel, options)
    print(result.text)
    

if __name__ == "__main__":
    sys.exit(int(main() or 0))