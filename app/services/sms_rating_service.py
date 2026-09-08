"""SMS post-call satisfaction rating service via Twilio."""

import logging
import os
from typing import Optional
from twilio.rest import Client

logger = logging.getLogger(__name__)


class SMSRatingService:
    """Send SMS satisfaction rating links after calls."""

    def __init__(self):
        """Initialize Twilio SMS service."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✅ SMS Rating Service initialized")
        else:
            self.client = None
            logger.warning("⚠️ Twilio SMS not configured")

    def send_satisfaction_rating(
        self,
        to_number: str,
        conversation_id: str,
        base_url: str = "https://your-domain.com"
    ) -> bool:
        """
        Send SMS with satisfaction rating link.

        Args:
            to_number: Phone number to send SMS to
            conversation_id: Unique conversation ID for tracking
            base_url: Base URL for rating link

        Returns:
            True if SMS sent successfully
        """
        if not self.client:
            logger.debug("⚠️ SMS not configured - skipping")
            return False

        try:
            # Create rating link
            rating_link = f"{base_url}/rate/{conversation_id}"

            # SMS message
            message_text = (
                f"Thank you for calling Bright Smile Dental Clinic! "
                f"How was your experience? "
                f"Rate us: {rating_link}"
            )

            # Send SMS
            message = self.client.messages.create(
                body=message_text,
                from_=self.from_number,
                to=to_number
            )

            logger.info(f"✅ Rating SMS sent to {to_number} (SID: {message.sid})")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending rating SMS: {e}")
            return False

    def is_available(self) -> bool:
        """Check if SMS service is configured."""
        return self.client is not None
