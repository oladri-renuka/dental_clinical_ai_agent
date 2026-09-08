import logging
import tempfile
import os
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper library not available")


class SpeechToTextService:
    """Speech-to-text using faster-whisper (local, 75ms latency)."""

    def __init__(self):
        self.model = None
        self.language = "en"

        if FASTER_WHISPER_AVAILABLE:
            try:
                # Load base model with int8 quantization for speed on CPU
                self.model = WhisperModel(
                    "base",
                    device="cpu",
                    compute_type="int8",
                    num_workers=1,
                )
                logger.info("✅ Faster-Whisper STT initialized (local, ~75ms per segment)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize faster-whisper: {e}")
        else:
            logger.warning("⚠️ faster-whisper not installed. Install with: pip install faster-whisper")

    def transcribe_audio(self, audio_bytes: bytes, language: str = "en") -> Optional[str]:
        """
        Transcribe audio bytes to text using faster-whisper (local).

        Args:
            audio_bytes: Raw audio data (WAV, MP3, etc.)
            language: Language code (default: 'en')

        Returns:
            Transcribed text or None on error
        """
        if not self.model:
            logger.error("❌ STT model not initialized")
            return None

        temp_file = None
        try:
            # Write audio bytes to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                temp_file = f.name

            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                temp_file,
                language=language,
                beam_size=1,  # Faster inference
            )

            # Collect all segments
            text = " ".join([segment.text for segment in segments]).strip()

            logger.debug(f"📝 Transcribed (faster-whisper): {text[:100]}...")
            return text if text else None

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

    def is_available(self) -> bool:
        """Check if STT service is available."""
        return self.model is not None


def get_stt_service():
    """Get STT service instance."""
    return SpeechToTextService()
