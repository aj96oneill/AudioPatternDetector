import logging

class Logger():
    def __init__(self,debug=False):
        self.debug = debug

    def set_up_logger(self):
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel("INFO")