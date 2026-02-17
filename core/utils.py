import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_sms(to, body):
    """
    Sends an SMS using Twilio if configured, otherwise logs to console.
    """
    if not settings.SMS_ENABLED:
        logger.info(f"SMS DISABLED: To={to}, Body={body}")
        return

    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

    if account_sid and auth_token and from_number:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=body,
                from_=from_number,
                to=to
            )
            logger.info(f"SMS SENT: SID={message.sid} To={to}")
            return True
        except Exception as e:
            logger.error(f"Twilio Error: {str(e)}")
            return False
    else:
        # Mock SMS for development
        print(f"\n[SMS MOCK] To: {to}\nMessage: {body}\n")
        logger.info(f"SMS MOCK: To={to}, Body={body}")
        return True
