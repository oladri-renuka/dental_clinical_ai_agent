from typing import TypedDict, Optional, List, Dict
from datetime import datetime

class Turn(TypedDict):
    """Single turn in conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime


class ConversationState(TypedDict):
    """State schema for LangGraph state machine."""
    conversation_id: str
    call_id: str  # Twilio call SID
    phone_number: Optional[str]

    # Conversation tracking
    conversation_history: List[Turn]
    turn_count: int
    start_time: datetime
    last_update: datetime

    # Intent and slots
    intent: Optional[str]  # book_appointment, cancel_appointment, etc.
    confidence: float  # 0.0-1.0
    slots: Dict[str, str]  # {name, date, time, reason, insurance_provider, etc.}

    # State flags
    resolved: bool
    escalated: bool
    escalation_reason: Optional[str]
    clarification_count: int  # Track number of clarifications

    # For sentiment tracking
    sentiment: Optional[str]  # positive, neutral, negative, angry
    consecutive_negative_sentiments: int  # Track consecutive negative sentiments for escalation

    # Control flags
    # Explicit slot tracking (ARCHITECTURAL FIX #2)
    collected_slots: Dict[str, str]  # Only slots that have been confirmed
    missing_slots: List[str]  # Slots still needed for this intent
    confirmation_sent: bool  # Track if confirmation has been asked

    # Control flags
    greeting_done: bool  # Track if greeting has been sent
