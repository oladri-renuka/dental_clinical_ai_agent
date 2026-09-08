import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Vonage Configuration
    VONAGE_API_KEY: str = os.getenv("VONAGE_API_KEY", "")
    VONAGE_API_SECRET: str = os.getenv("VONAGE_API_SECRET", "")
    VONAGE_PHONE_NUMBER: str = os.getenv("VONAGE_PHONE_NUMBER", "")

    # Twilio Configuration (legacy)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # OpenRouter Configuration (for Claude via OpenRouter)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = os.getenv("LLM_MODEL", "anthropic/claude-3-5-sonnet")

    # ElevenLabs Configuration (Flash model - 75ms latency)
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Any voice ID

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dental_clinic.db")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
