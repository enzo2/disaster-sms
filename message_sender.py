import smtplib
from email.message import EmailMessage
import os
import logging
from dotenv import load_dotenv
load_dotenv()
from twilio.rest import Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL') if os.getenv('ADMIN_EMAIL') else None

# sends email using SMTP
# default recipient is the admin
def send_email(message, subject="", recipients=None):
    if recipients is None and ADMIN_EMAIL is not None:
        recipients = [ADMIN_EMAIL]
    elif recipients is None:
        logger.error("No recipients provided for email")
        return
    
    logger.info(f"Sending email to {recipients}")
    
    relay_host = os.getenv('RELAYHOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_pwd = os.getenv('SMTP_PWD')
    sender_domain = os.getenv('SENDER_DOMAIN')

    if not all([relay_host, smtp_user, smtp_pwd, sender_domain]):
        logger.error("Required environment variables for SMTP relay are not set")
        return

    try:
        # The relay host is expected in "hostname:port" format
        host, port = relay_host.split(':')
        port = int(port)
        
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_pwd)
            
            for recipient in recipients:
                msg = EmailMessage()
                msg['From'] = f'system@{sender_domain}'
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.set_content(message)
                
                logger.info(f"Sending email via SMTP relay to: {recipient}")
                smtp.send_message(msg)
                
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def send_sms(body, to_phone_number):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, from_phone_number]):
        logger.error("Twilio credentials not configured.")
        return

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_phone_number,
            to=to_phone_number
        )
        logger.info(f"SMS sent to {to_phone_number}: {message.sid}")
    except Exception as e:
        logger.error(f"Error sending SMS to {to_phone_number}: {e}")

# Usage examples:
# send_sms(summary, to_phone_number)  # For regular messages
# send_email(error_message, 'Disaster Info System Error', recipients=[os.getenv('ADMIN_EMAIL')])  # For error messages
# send_sms('Test message', to_phone_number)  # For test messages
