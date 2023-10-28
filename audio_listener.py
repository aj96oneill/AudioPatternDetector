import pyaudio
import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
import smtplib
import logging
import time
from datetime import datetime
from gpiozero import CPUTemperature
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

RATE = 44100
# Roughly 4 seconds of audio capture
CHUNK = 1024 * 172
# If set to true, a fft graph will be displayed if any peaks cross the minimum threshold
DEBUG = False

class Listener():
    def __init__(self, picture_evidence=False):
        self.sender_email = ""
        self.reciver_email = ""
        self.email_pwd = ""
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.set_up_logger()
        self.connect_audio_device()
        self.logger.info(f"Chunk size is {CHUNK}")
        self.cpu = CPUTemperature()
        self.last_time = None
        self.take_picture = picture_evidence
        self.img_path = "./img.png"

    def set_up_logger(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel("INFO")

    def connect_audio_device(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    def print_fft(self, fourier, cut=False):
        total_len = 44000
        arr_len = len(fourier)
        if cut:
            total_len = total_len // 2
            arr_len = arr_len // 2

        w = np.linspace(0, total_len, arr_len)

        # First half is the real component, second half is imaginary
        fourier_to_plot = fourier[0:arr_len]
        w = w[0:arr_len]

        plt.figure(1)

        plt.plot(w, fourier_to_plot)
        plt.xlabel('frequency')
        plt.ylabel('amplitude')
        plt.show()

    def send_email(self, subject, message):
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.reciver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, 'plain'))

        if self.take_picture:
            self.logger.info("Taking picture for email")
            self.take_pic()
            time.sleep(1)
            with open(self.img_path, 'rb') as img_file:
                img = MIMEImage(img_file.read(), name='live_capture.png')
                msg.attach(img)

        try:
            self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.server.starttls()
            self.server.login(self.sender_email, self.email_pwd)
            self.server.sendmail(self.sender_email, self.reciver_email, msg.as_string())
            self.logger.info("Email sent.")
            self.server.quit()
        except Exception as e:
            self.logger.error(f"email failed to send: {str(e)}")
    def take_pic(self):
        cap = cv2.VideoCapture(0)
        ret,frame = cap.read()
        cv2.imwrite(self.img_path, frame)
    
    def check_for_noise(self, audio_data):
        fourier_audio = np.fft.fft(audio_data)
        fourier_audio = fourier_audio[0:len(fourier_audio)//2].real

        w = np.linspace(0, 44000, len(fourier_audio))
        audio_avg = np.mean(np.abs(fourier_audio))
        thresh = 15_000_000
        amp = fourier_audio[0:len(fourier_audio)//2]
        freq = w[0:len(fourier_audio)//2]
        pairs = zip(freq, amp)
        peak_1 = []
        peak_2 = []
        peak_3 = []
        peak_4 = []
        for f,a in pairs:
            if 1100<f<1600:
                peak_1.append(a)
            elif 800<f<1100:
                peak_2.append(a)
            elif 2000<f<2700:
                peak_3.append(a)
            elif 9000<f<9800:
                peak_4.append(a)

        p1 = max(peak_1)
        p2 = max(peak_2)
        p3 = max(peak_3)
        p4 = max(peak_4)
        msg_pattern_test = (p1 > p2 > p3 and p3 > audio_avg and p3 > thresh) \
                or (p2 > p3 > p1 and p1 > audio_avg and p1 > thresh) \
                or (p1 > p3 > p2 and p2 > audio_avg and p2 > thresh)

        call_pattern_test = p2 > p1 and p2 > p3 and p2 > thresh and p2 > 1000*audio_avg

        email_pattern_test = p4 > (thresh / 10) and (p3 > p4 or p4 > 130*audio_avg)

        if msg_pattern_test:
            self.logger.info("WINNER: MSG pattern")
            self.send_email("Msg pattern detected", "check laptop for teams message")
        if call_pattern_test:
            self.logger.info("WINNER: CALL pattern")
            check = self.check_ready_to_send(datetime.now())
            if check:
                pass
                self.send_email("Call pattern detected", "check laptop for teams call")
            else:
                self.logger.info("Hasn't been long enough. No email will be sent.")
        if email_pattern_test:
            self.logger.info("WINNER: EMAIL pattern")
            self.send_email("Email pattern detected", "check laptop for email")

        # General louder audio detection - use for deubugging and finding patterns
        if DEBUG:
            threshold = 5_000_000
            peaks, _ = find_peaks(fourier_audio, height=threshold)
            # self.logger.info(peaks)
            # self.logger.info(fourier_audio[peaks])

            if len(peaks) > 0:
                self.logger.info(f"WINNER: {len(peaks)} peaks detected above {threshold}")
                self.logger.info(peaks)
                self.logger.info(fourier_audio[peaks])
                self.print_fft(fourier_audio)
    
    def check_ready_to_send(self, current_time):
        if self.last_time is None:
            self.last_time = current_time
            return True
        # if its been 15 seconds from most recent detection, then allow new notification
        elif (current_time - self.last_time).seconds > 15:
            self.last_time = current_time
            return True
        else:
            self.last_time = current_time
            return False
        
    def run(self):
        self.logger.info("Listening...")
        try:
            while True:
                if self.cpu.temperature < 75:
                    audio_data = np.frombuffer(self.stream.read(CHUNK), dtype=np.int16)
                    self.check_for_noise(audio_data)
                else:
                    self.send_email("Pi Getting Hot", f"Temp was {self.cpu.temperature}. Sleeping for 30 sec")
                    time.sleep(30)
        except KeyboardInterrupt:
            self.logger.info("Stopping listener")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

if __name__ == "__main__":
    Listener(picture_evidence=True).run()