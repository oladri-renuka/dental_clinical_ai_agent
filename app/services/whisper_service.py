"""Faster-Whisper STT service for streaming audio transcription (local CPU, free)."""

import logging
from typing import Optional
import io

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed, STT will fail")


class WhisperService:
    """Speech-to-text using faster-whisper (local, no API key required)."""

    def __init__(self):
        """Initialize Faster-Whisper service with local model."""
        self.model = None
        if FASTER_WHISPER_AVAILABLE:
            try:
                # Load small model (~140MB) for faster inference on CPU
                # Models: tiny, base, small, medium, large
                self.model = WhisperModel("base", device="cpu", compute_type="int8")
                logger.info("✅ Faster-Whisper model loaded (base, CPU)")
            except Exception as e:
                logger.error(f"❌ Error loading Whisper model: {e}")
                self.model = None

    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio bytes to text using faster-whisper.

        Args:
            audio_data: Raw audio bytes (WAV/MP3 format)

        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.model:
            logger.error("❌ Whisper model not available")
            return None

        try:
            # Save audio to temporary file (faster-whisper needs file path)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Transcribe
            segments, info = self.model.transcribe(tmp_path, language="en")
            text = " ".join([segment.text for segment in segments]).strip()

            # Clean up temp file
            import os
            os.unlink(tmp_path)

            logger.info(f"✅ Transcribed: {text[:80]}")
            return text if text else None

        except Exception as e:
            logger.error(f"❌ Whisper transcription error: {e}")
            return None

    def transcribe_file(self, file_path: str) -> Optional[str]:
        """Transcribe audio file."""
        try:
            with open(file_path, "rb") as f:
                return self.transcribe_audio(f.read())
        except Exception as e:
            logger.error(f"❌ Error reading audio file: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Whisper is available."""
        return self.model is not None
