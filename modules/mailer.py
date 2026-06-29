# modules/mailer.py
import time
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Tuple, Dict
from pathlib import Path
import config

class ZeroCostMailer:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password

    def _get_html_body(self, name: str) -> str:
        return f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
            <p>Dear <strong>{name}</strong>,</p>
            <p>Congratulations! Please find attached your official verified certificate of completion.</p>
            <p>If you notice any discrepancies in the spelling of your name, please reply directly to this email.</p>
            <br>
            <p>Best regards,<br><strong>The CertiFlow Dispatch Team</strong></p>
          </body>
        </html>
        """

    def send_certificate(self, target_email: str, recipient_name: str, pdf_path: str, is_dry_run: bool = False) -> Tuple[bool, str]:
        path_obj = Path(pdf_path)
        if not path_obj.exists():
            return False, "Attachment error: Generated PDF path unlocatable on disk."

        msg = MIMEMultipart()
        msg["From"] = self.user
        msg["To"] = target_email
        msg["Subject"] = f"Your Verified Certificate of Completion - {recipient_name}"

        body = self._get_html_body(recipient_name)
        msg.attach(MIMEText(body, "html"))

        try:
            with open(path_obj, "rb") as f:
                part = MIMEApplication(f.read(), _subtype="pdf")
                part.add_header("Content-Disposition", "attachment", filename=path_obj.name)
                msg.attach(part)
        except Exception as e:
            return False, f"File read error: {str(e)}"

        try:
            server = smtplib.SMTP(self.host, self.port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.user, self.password)
            server.sendmail(self.user, target_email, msg.as_string())
            server.quit()

            if not is_dry_run:
                jitter = random.uniform(config.JITTER_MIN, config.JITTER_MAX)
                time.sleep(jitter)

            return True, "Dispatched OK"
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP Auth Failed: Check Username or App Password."
        except Exception as e:
            return False, f"Network/SMTP Error: {str(e)}"