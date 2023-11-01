import smtplib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


class EMailInterface():
    def __init__(self, logger, payload):
        self.sender_email = payload.get("sender_email", "")
        self.reciever_email = payload.get("reciever_email", "")
        self.reciever_phone = payload.get("reciever_phone", "")
        self.email_pwd = payload.get("email_pwd", "")
        self.smtp_server = payload.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = payload.get("smtp_port", 587) 
        self.txt_gate = payload.get("txt_gate", "") 
        self.multi_media_gate = payload.get("multi_media_gate", "")
        self.logger = logger

    def send_email(self, subject, message="", evidence=None, debug_img=None):
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.reciever_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, 'plain'))

        if evidence:
            # self.logger.info("Taking picture for email")
            # self.take_pic()
            # time.sleep(1)
            with open(evidence, 'rb') as img_file:
                img_data = img_file.read()
                img_encoded = base64.b64encode(img_data).decode('utf-8')
                img = MIMEImage(base64.b64decode(img_encoded), name='live_capture.png')
                msg.attach(img)

        if debug_img:
            with open(debug_img, 'rb') as img_file:
                img_data = img_file.read()
                img_encoded = base64.b64encode(img_data).decode('utf-8')
                img = MIMEImage(base64.b64decode(img_encoded), name='audio.png')
                msg.attach(img)
        try:
            self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.server.starttls()
            self.server.login(self.sender_email, self.email_pwd)
            self.server.sendmail(self.sender_email, self.reciever_email, msg.as_string())
            self.logger.info("Email sent.")
            self.server.quit()
        except Exception as e:
            self.logger.error(f"email failed to send: {str(e)}")

    def send_text(self, subject, message="", evidence=None, debug_img=None):
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.reciever_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, 'plain'))
        gate = self.multi_media_gate if evidence or debug_img else self.txt_gate
        mobile_gateway = f"{self.reciever_phone}@{gate}"

        if evidence:
            with open(evidence, 'rb') as img_file:
                img_data = img_file.read()
                img_encoded = base64.b64encode(img_data).decode('utf-8')
                img = MIMEImage(base64.b64decode(img_encoded), name='live_capture.png')
                msg.attach(img)

        if debug_img:
            with open(debug_img, 'rb') as img_file:
                img_data = img_file.read()
                img_encoded = base64.b64encode(img_data).decode('utf-8')
                img = MIMEImage(base64.b64decode(img_encoded), name='audio.png')
                msg.attach(img)

        try:
            self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.server.starttls()
            self.server.login(self.sender_email, self.email_pwd)
            self.server.sendmail(self.sender_email, [mobile_gateway], msg.as_string())
            self.logger.info("Text sent.")
            self.server.quit()
        except Exception as e:
            self.logger.error(f"Text from smtp failed to send: {str(e)}")