import logging
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import torch
import whisper

import utils

def main():
    logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(filename)s - %(funcName)s: %(message)s', level=logging.INFO)

    # Startup health check
    utils.check_torch()
    whisper_model = utils.check_whisper()
    whisper_options = whisper.DecodingOptions(fp16=False, language='en') # en / ja

    audio = utils.capture_microphone()

    running = True
    while (running):
        try:
            # Start recording
            time.sleep(10)

            nparray = audio.get_nparray()
            # clear buffer to prepare for the next loop
            audio.frames = b''
            audio.chunk_data = ''


            # downsample (mandatory?)
            nparray = utils.downsample(nparray)

            # memory usage increases when using matplotlib
            utils.generate_waveform(nparray)

            N_SAMPLES = 480000 # this should be fixed (16000*30), as the model expects 16000Hz for 30s.
            real_audio = whisper.pad_or_trim(nparray, length=N_SAMPLES)

            mel = whisper.log_mel_spectrogram(real_audio, padding=int(N_SAMPLES - real_audio.shape[0])).to(whisper_model.device)

            result = whisper.decode(whisper_model, mel, whisper_options)
            print(result.text)
        except KeyboardInterrupt:
            running = False
        except Exception as e:
            logging.critical(e)
            break
    audio.stop()

if __name__ == "__main__":
    sys.exit(int(main() or 0))