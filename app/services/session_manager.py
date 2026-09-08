import json
import logging
from typing import Optional, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory fallback")


class SessionManager:
    """Manages conversation state using Redis or in-memory fallback."""

    def __init__(self):
        self.redis_client = None
        self.fallback_storage = {}  # In-memory fallback
        self.ttl_seconds = 86400  # 24 hours

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Connected to Redis")
            except Exception as e:
                logger.warning(f"❌ Failed to connect to Redis: {e}. Using in-memory fallback.")
                self.redis_client = None

    def save_state(self, call_id: str, state: Dict[str, Any]) -> bool:
        """Save conversation state with TTL."""
        try:
            state_json = json.dumps(state, default=str)  # Handle datetime serialization

            if self.redis_client:
                self.redis_client.setex(call_id, self.ttl_seconds, state_json)
            else:
                self.fallback_storage[call_id] = state_json

            logger.debug(f"💾 Saved state for call {call_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving state for {call_id}: {e}")
            return False

    def load_state(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from Redis or fallback."""
        try:
            if self.redis_client:
                state_json = self.redis_client.get(call_id)
            else:
                state_json = self.fallback_storage.get(call_id)

            if not state_json:
                logger.debug(f"⚠️ No state found for call {call_id}")
                return None

            state = json.loads(state_json)
            logger.debug(f"📖 Loaded state for call {call_id}")
            return state
        except Exception as e:
            logger.error(f"❌ Error loading state for {call_id}: {e}")
            return None

    def delete_state(self, call_id: str) -> bool:
        """Delete conversation state."""
        try:
            if self.redis_client:
                self.redis_client.delete(call_id)
            else:
                self.fallback_storage.pop(call_id, None)

            logger.debug(f"🗑️ Deleted state for call {call_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting state for {call_id}: {e}")
            return False

    def cleanup_expired(self) -> int:
        """Cleanup expired sessions (only applicable for fallback storage)."""
        if not self.redis_client:
            # Redis handles TTL automatically
            # For fallback, we'd need to track timestamps - not implemented
            return 0
        return 0


# Global session manager instance
session_manager = SessionManager()
