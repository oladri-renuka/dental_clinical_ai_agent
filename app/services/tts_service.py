import logging
from typing import Optional
from io import BytesIO
from config.settings import settings

logger = logging.getLogger(__name__)

try:
    from elevenlabs import ElevenLabs, VoiceSettings
    from elevenlabs.client import ElevenLabs as ElevenLabsClient
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("ElevenLabs library not available")


class TextToSpeechService:
    """Text-to-speech using ElevenLabs Flash model (75ms latency)."""

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.client = None

        if ELEVENLABS_AVAILABLE and self.api_key:
            try:
                self.client = ElevenLabsClient(api_key=self.api_key)
                logger.info("✅ ElevenLabs TTS initialized (Flash model - 75ms latency)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ElevenLabs: {e}")
        elif not self.api_key:
            logger.warning("⚠️ ELEVENLABS_API_KEY not set")

    def synthesize(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to speech audio using ElevenLabs Flash model.
        Returns: Audio bytes (MP3 format)
        """
        if not self.client:
            logger.error("❌ TTS client not initialized")
            return None

        try:
            voice_id = voice_id or self.voice_id

            audio = self.client.generate(
                text=text,
                voice=voice_id,
                model="eleven_flash_v2",  # Flash model: 75ms latency for real-time phone
            )

            # Collect audio bytes
            audio_bytes = BytesIO()
            for chunk in audio:
                audio_bytes.write(chunk)

            audio_bytes.seek(0)
            logger.debug(f"🔊 Generated audio (Flash) for: {text[:50]}...")
            return audio_bytes.getvalue()

        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if TTS service is available."""
        return self.client is not None


# Fallback TTS responses (for when ElevenLabs is unavailable)
FALLBACK_RESPONSES = {
    "greeting": "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?",
    "error": "I'm sorry, I didn't understand that. Could you please repeat?",
    "escalation": "I'm connecting you with a team member. Please hold.",
    "confirm": "Is this information correct?",
}


def get_tts_service():
    """Get TTS service instance."""
    return TextToSpeechService()
