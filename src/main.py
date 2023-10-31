import time
import json
import numpy as np
from gpiozero import CPUTemperature

from utils.audio_listener import Listener
from utils.camera import Camera
from utils.notifications import EMailInterface
from utils.logger import Logger

DEBUG = False
ENRICH = True
TEXT = True
EMAIL = True
PIC = True


if __name__ == "__main__":
    with open('config.json') as json_file:
        payload = json.load(json_file)
    logger = Logger(debug=DEBUG).set_up_logger()
    ears = Listener(logger)
    eyes = Camera(logger)
    mouth = EMailInterface(logger, payload)
    brain = CPUTemperature()
    try:
        logger.info("Listening...")
        while True:
            if brain.temperature < 75:
                audio_data = np.frombuffer(ears.stream.read(ears.chunk), dtype=np.int16)
                resp = ears.check_for_noise(audio_data)
                if resp:
                    subject = resp.get("subj", "Something Detected")
                    message = resp.get("msg", "Check laptop.")
                    pic_path = None
                    audio_path = None
                    if PIC:
                        pic_path = eyes.take_pic()
                        time.sleep(0.5)
                    if TEXT:
                        # I only ever want fft img and enriched msg in email
                        mouth.send_text(subject, message, pic_path, audio_path)
                    if ENRICH:
                        message = message +"\n"+ str(resp["data"])
                        audio_path = ears.save_fft(resp["audio"])
                    if EMAIL:
                        mouth.send_email(subject, message, pic_path, audio_path)
            else:
                mouth.send_email("Pi Getting Hot", f"Temp was {brain.temperature}C. Sleeping for 30 sec")
                time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Stopping listener")