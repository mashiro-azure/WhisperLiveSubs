import logging
import sys
from queue import Queue

import utils
import whisper


def main():
    log = logging.getLogger("logger")
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(filename)s - %(funcName)s: %(message)s",
        level=logging.INFO,
    )

    # Startup health check
    device = utils.check_torch()
    whisper_model = utils.check_whisper(model_size="base", device=device)
    whisper_options = whisper.DecodingOptions(fp16=False, language="en", task="transcribe")  # en / ja

    audio_queue = Queue()
    audio = utils.capture_microphone(eventQueue=audio_queue)
    audio.set_volThreshold(1500)
    # audio.set_voiceActivityLengthMS(2000)
    audio.set_voiceTimeoutMS(1000)

    running = True
    while running:
        try:
            # Start recording
            # time.sleep(10)
            audio_queue_event = audio_queue.get()
            if audio_queue_event["audio_buffer"] == "full":
                audio_tensor = audio.get_audioTensor()

                # downsample (mandatory?)
                audio_tensor = utils.downsample(audio_tensor, audio.rate)

                # memory usage increases when using matplotlib
                utils.generate_waveform(audio_tensor, (audio.volThreshold / 32768.0))

                N_SAMPLES = 480000  # this should be fixed (16000*30), as the model expects 16000Hz for 30s.
                padded_audio = whisper.pad_or_trim(audio_tensor, length=N_SAMPLES)

                mel = whisper.log_mel_spectrogram(padded_audio).to(whisper_model.device)

                result = whisper.decode(whisper_model, mel, whisper_options)
                print(f"Whisper Output: {result.text}")
        except KeyboardInterrupt:
            running = False
            log.info("Keyboard Interrupt detected, quitting.")
        except Exception as e:
            log.critical(e)
            break
    audio.stop()


if __name__ == "__main__":
    sys.exit(int(main() or 0))
