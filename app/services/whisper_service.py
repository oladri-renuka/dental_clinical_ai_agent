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
        """Initialize Faster-Whisper service (lazy-loaded)."""
        self._model = None
        logger.info("📝 WhisperService initialized (lazy-loaded, will load on first use)")

    def _get_model(self):
        """Lazy-load Whisper model on first use."""
        if self._model is None:
            if not FASTER_WHISPER_AVAILABLE:
                logger.warning("faster-whisper not available")
                return None
            try:
                logger.info("📥 Loading Faster-Whisper model (base, CPU) - this takes ~30 seconds on first run...")
                self._model = WhisperModel("base", device="cpu", compute_type="int8")
                logger.info("✅ Faster-Whisper model loaded successfully!")
            except Exception as e:
                logger.error(f"❌ Error loading Whisper model: {e}")
                return None
        return self._model

    @property
    def model(self):
        """Get or load the Whisper model."""
        return self._get_model()

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
