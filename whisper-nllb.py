import logging
import sys
import time

import queue

import whisper

import utils

def main():
    logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(filename)s - %(funcName)s: %(message)s', level=logging.INFO)

    # Startup health check
    utils.check_torch()
    whisper_model = utils.check_whisper(model_size='base')
    whisper_options = whisper.DecodingOptions(fp16=False, language='en') # en / ja

    audio_queue = queue.Queue()
    audio = utils.capture_microphone(queue=audio_queue)
    audio.set_volThreshold(1500)
    # audio.set_voiceActivityLengthMS(2000)
    audio.set_voiceTimeoutMS(1000)

    running = True
    while (running):
        try:
            # Start recording
            # time.sleep(10)
            audio_queue_event = audio_queue.get()
            if audio_queue_event['audio_buffer'] == 'full':
                nparray = audio.get_nparray()

                # downsample (mandatory?)
                nparray = utils.downsample(nparray)

                # memory usage increases when using matplotlib
                utils.generate_waveform(nparray, (audio.volThreshold/32768.0))

                N_SAMPLES = 480000 # this should be fixed (16000*30), as the model expects 16000Hz for 30s.
                real_audio = whisper.pad_or_trim(nparray, length=N_SAMPLES)

                mel = whisper.log_mel_spectrogram(real_audio, padding=int(N_SAMPLES - real_audio.shape[0])).to(whisper_model.device)

                result = whisper.decode(whisper_model, mel, whisper_options)
                print(f"Whisper Output: {result.text}")
        except KeyboardInterrupt:
            running = False
            logging.info("Keyboard Interrupt detected, quitting.")
        except Exception as e:
            logging.critical(e)
            break
    audio.stop()

if __name__ == "__main__":
    sys.exit(int(main() or 0))