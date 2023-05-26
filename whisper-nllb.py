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

    real_audio = audio.get_nparray()
    audio.stop()
    ## matplotlib
    fig = plt.figure()
    s = fig.add_subplot()
    s.plot(real_audio)
    fig.savefig('fig.jpg')
    ## matplotlib

    real_audio = whisper.pad_or_trim(real_audio)

    mel = whisper.log_mel_spectrogram(real_audio).to(whisper_model.device)
    _, probs = whisper_model.detect_language(mel)

    print(f"Detected language: {max(probs, key=probs.get)}")

    options = whisper.DecodingOptions(fp16=False)
    result = whisper.decode(whisper_model, mel, options)
    print(result.text)
    

if __name__ == "__main__":
    sys.exit(int(main() or 0))