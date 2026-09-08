"""Vonage Voice API service for handling phone calls."""

import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VonageService:
    """Vonage Voice API handler for incoming/outgoing calls."""

    def __init__(self):
        """Initialize Vonage service with API credentials."""
        self.api_key = os.getenv("VONAGE_API_KEY")
        self.api_secret = os.getenv("VONAGE_API_SECRET")
        self.phone_number = os.getenv("VONAGE_PHONE_NUMBER")

        if not all([self.api_key, self.api_secret, self.phone_number]):
            logger.warning("⚠️ Vonage credentials not fully configured")

        self.base_url = "https://api.nexmo.com/v1"
        logger.info(f"✅ Vonage service initialized with number {self.phone_number}")

    def generate_ncco(self, message: str) -> list:
        """
        Generate NCCO (Nexmo Call Control Object) for voice response.

        Args:
            message: Text to speak to the caller

        Returns:
            NCCO array for Vonage Voice API
        """
        return [
            {
                "action": "talk",
                "text": message,
                "voiceName": "Amy",  # British female voice
            }
        ]

    def create_answer_ncco(self) -> list:
        """Create NCCO for answering and recording a call."""
        return [
            {
                "action": "talk",
                "text": "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?",
                "voiceName": "Amy",
            },
            {
                "action": "input",
                "type": "speech",
                "timeout": 5,
                "speechTimeout": "auto",
                "startOnSilence": 3000,
                "language": "en-US",
                "eventUrl": ["https://your-domain.com/vonage-speech-input"],
            }
        ]

    def is_available(self) -> bool:
        """Check if Vonage service is properly configured."""
        return bool(self.api_key and self.api_secret and self.phone_number)

    def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header for Vonage API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json",
        }


# Global instance
vonage_service = VonageService()
