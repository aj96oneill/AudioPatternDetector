import logging

class Logger():
    def __init__(self,debug=False):
        self.debug = debug

    def set_up_logger(self, name="AudioDetector"):
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(name)
        self.logger.setLevel("INFO")
        return self.logger