"""ElevenLabs text-to-speech service using Flash v2 (free tier, fast)."""

import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """Text-to-speech using ElevenLabs Flash v2 API (free tier)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize ElevenLabs service with Flash v2 (fastest + free tier)."""
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        # Use a default professional voice (Rachel)
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        # Flash v2: 10x faster, 50% cheaper, free tier 10k chars/month
        self.model_id = "eleven_flash_v2"

    def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech audio using Flash v2 (faster + cheaper).

        Args:
            text: Text to convert to speech

        Returns:
            Audio bytes in MP3 format or None if conversion fails
        """
        if not self.api_key:
            logger.debug("⚠️ ElevenLabs API key not set - using Twilio voice fallback")
            return None

        try:
            import requests

            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            data = {
                "text": text,
                "model_id": self.model_id,  # Flash v2 for speed
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                logger.info(f"✅ TTS generated: {text[:50]}... (Flash v2)")
                return response.content  # MP3 bytes
            elif response.status_code == 429:
                logger.warning(f"⚠️ ElevenLabs quota exceeded - using Twilio fallback")
                return None
            else:
                logger.error(f"❌ ElevenLabs error: {response.status_code} {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            return None

    def is_available(self) -> bool:
        """Check if ElevenLabs service is available and has quota."""
        if not self.api_key:
            return False
        # Could add quota check here if needed
        return True
