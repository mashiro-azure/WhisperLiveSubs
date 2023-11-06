import logging
import queue
import threading

import whisper

from backend import utils

log = logging.getLogger("logger")
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s]: %(filename)s - %(funcName)s: %(message)s",
    level=logging.INFO,
)


class whisperProcessing(threading.Thread):
    def __init__(self, userSettings: dict, readyEvent: threading.Event, outputQueue: queue.Queue) -> None:
        threading.Thread.__init__(self)
        self.name = "Whisper Inference"
        self.device, self.fp16 = utils.check_torch(userSettings["WhisperGPU"])
        self.whisper_model = utils.check_whisper(model_size=userSettings["WhisperModelSize"], device=self.device)
        self.whisper_options = whisper.DecodingOptions(
            fp16=self.fp16,
            language=userSettings["WhisperLanguage"],
            task=userSettings["WhisperTask"],
        )
        self.audio_queue = queue.Queue()
        self.audio = utils.capture_microphone(eventQueue=self.audio_queue, userSettings=userSettings)
        self.audio.set_volThreshold(int(userSettings["VolumeThreshold"]))
        self.audio.set_voiceTimeoutMS(int(userSettings["VoiceTimeout"]))
        self.outputQueue = outputQueue
        self.running = True
        readyEvent.set()

    def run(self):
        while self.running is True:
            try:
                # Start recording
                # time.sleep(10)
                audio_queue_event = self.audio_queue.get()
                if audio_queue_event["audio_buffer"] == "full":
                    audio_tensor = self.audio.get_audioTensor()

                    # downsample (mandatory?)
                    audio_tensor = utils.downsample(audio_tensor, self.audio.rate)

                    # memory usage increases when using matplotlib
                    # utils.generate_waveform(audio_tensor, (self.audio.volThreshold / 32768.0))

                    N_SAMPLES = 480000  # this should be fixed (16000*30), as the model expects 16000Hz for 30s.
                    padded_audio = whisper.pad_or_trim(audio_tensor, length=N_SAMPLES)

                    mel = whisper.log_mel_spectrogram(padded_audio).to(self.whisper_model.device)

                    result = whisper.decode(self.whisper_model, mel, self.whisper_options)
                    try:
                        self.outputQueue.put(result.text, block=False)
                    except queue.Full:
                        pass
                    print(f"Whisper Output: {result.text}")
            except KeyboardInterrupt:
                self.running = False
                log.info("Keyboard Interrupt detected, quitting.")
            except Exception as e:
                log.critical(e)
                raise

    def stop(self):
        self.audio.stop()
        self.running = False
        log.info("Whisper inference stopping normally.")
