import cv2


class Camera():
    def __init__(self, logger, target_path="."):
        self.logger = logger
        self.img_path = target_path
    
    def take_pic(self, pic_name="img.png"):
        self.logger.debug("Taking picture...")
        cap = cv2.VideoCapture(0)
        ret,frame = cap.read()
        save_location = f"{self.img_path}/{pic_name}"
        self.logger.debug(f"Saving picture to: {save_location}")
        cv2.imwrite(save_location, frame)
        return save_location