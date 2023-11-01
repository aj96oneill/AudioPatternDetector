import pyaudio

import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime
from scipy.signal import find_peaks

from utils.logger import Logger

class Listener():
    def __init__(self, logger):
        self.rate = 44100
        # Roughly 4 seconds of audio capture
        self.chunk = 1024 * 172
        self.logger = logger
        self.connect_audio_device()
        self.logger.debug(f"Chunk size is {self.chunk}")
        self.last_time = None

    def connect_audio_device(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk)

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

    def save_fft(self, fourier, cut=False, path=".", name="fft.png"):
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
        save_path = f"{path}/{name}"
        plt.savefig(save_path)
        plt.close()
        return save_path
    
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

        response ={
            "audio": fourier_audio,
            "data" : {
                "avg": audio_avg,
                "threshold": thresh,
                "P1(1100-1600)": p1,
                "P2(800-1100)": p2,
                "P3(2000-2700)": p3,
                "P4(9000-9800)": p4
            }
        }

        if msg_pattern_test:
            self.logger.info("WINNER: MSG pattern")
            response["subj"] = "Msg pattern detected"
            response["msg"] = "check laptop for teams message"
            return response
        if call_pattern_test:
            self.logger.info("WINNER: CALL pattern")
            ready = self.check_ready_to_send(datetime.now())
            if ready:
                response["subj"] = "Call pattern detected"
                response["msg"] = "check laptop for teams call"
                return response
            else:
                self.logger.info("Hasn't been long enough. No message will be sent.")
                return None
        if email_pattern_test:
            self.logger.info("WINNER: EMAIL pattern")
            response["subj"] = "Email pattern detected"
            response["msg"] = "check laptop for email"
            return response
        return None
    
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
        
    def __del__(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

if __name__ == "__main__":
    # General louder audio detection - use for deubugging and finding patterns
    logger = Logger(debug=False).set_up_logger()
    ears = Listener(logger)
    while True:
        audio_data = np.frombuffer(ears.stream.read(ears.chunk), dtype=np.int16)

        fourier_audio = np.fft.fft(audio_data)
        fourier_audio = fourier_audio[0:len(fourier_audio)//2].real

        threshold = 5_000_000
        peaks, _ = find_peaks(fourier_audio, height=threshold)
        # self.logger.info(peaks)
        # self.logger.info(fourier_audio[peaks])

        if len(peaks) > 0:
            logger.info(f"WINNER: {len(peaks)} peaks detected above {threshold}")
            logger.info(peaks)
            logger.info(fourier_audio[peaks])
            Listener(None).print_fft(fourier_audio)