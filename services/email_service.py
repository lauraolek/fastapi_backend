import logging
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

# Configuration - In a real app, use environment variables!
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")  # e.g., smtp.mailgun.org or smtp.sendgrid.net
SMTP_PORT = os.environ.get("SMTP_PORT", 587)                 # Use 587 for STARTTLS
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "your-email@example.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "your-app-password")  # Never use your real password; use an App Password
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "your-email@example.com")

class EmailService:
    def __init__(self):
        self.server = SMTP_SERVER
        self.port = int(SMTP_PORT)
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD

    def send_pin_reset_email(self, recipient_email: str, new_pin: str):
        """
        Constructs and sends a PIN update email via SMTP.
        """
        # 1. Create the message container
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Secure PIN has been updated"
        message["From"] = SENDER_EMAIL
        message["To"] = recipient_email

        # 2. Create the body (Plain text and HTML)
        text = f"Hello,\n\nYour new security PIN is: {new_pin}\n\nIf you did not request this, please contact support."
        html = f"""
        <html>
            <body>
                <h2>Security Update</h2>
                <p>Hello,</p>
                <p>Your new security PIN is: <strong>{new_pin}</strong></p>
                <p style="color: red;">If you did not request this, please contact support immediately.</p>
            </body>
        </html>
        """

        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        # 3. Send the email
        # We use a context manager to ensure the connection is closed
        context = ssl.create_default_context()
        
        try:
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls(context=context) # Secure the connection
                server.login(self.username, self.password)
                server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
            logger.info(f"Email sent successfully to {recipient_email}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
