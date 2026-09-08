"""Structured slot extraction using Pydantic models and regex/keyword matching."""

import re
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Intent slot requirements
class BookAppointmentSlots(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    reason: Optional[str] = None

class CancelAppointmentSlots(BaseModel):
    name: Optional[str] = None
    appointment_id_or_date: Optional[str] = None

class RescheduleSlots(BaseModel):
    name: Optional[str] = None
    appointment_id_or_date: Optional[str] = None
    new_date: Optional[str] = None
    new_time: Optional[str] = None

class InsuranceQuestionSlots(BaseModel):
    name: Optional[str] = None

# Slot extraction logic
def extract_name(text: str) -> Optional[str]:
    """Extract patient name from text."""
    if not text:
        return None

    # Pattern 1: Explicit name patterns ("my name is X", "I'm X", "call me X")
    name_match = re.search(
        r"(?:my name is|i'?m|call me|it'?s|name'?s)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        text,
        re.IGNORECASE
    )
    if name_match:
        return name_match.group(1)

    # Pattern 2: Look for capitalized word pairs (FirstName LastName) anywhere in text
    # This handles cases where the name appears after common words
    words = text.split()

    # Appointment reason words to exclude
    appointment_reasons = {"Regular", "Emergency", "Cleaning", "Checkup", "Exam", "Whitening",
                          "Root", "Filling", "Extraction", "Urgent", "Same", "Next"}

    for i in range(len(words) - 1):
        word = words[i].rstrip(",.:;!?")
        next_word = words[i + 1].rstrip(",.:;!?")

        # Check if we have two capitalized words that look like a name
        if (word and word[0].isupper() and len(word) > 2 and
            next_word and next_word[0].isupper() and len(next_word) > 2):

            # Exclude common patterns and appointment-related words
            common_words = {"The", "And", "But", "That", "This", "From", "With", "Have"}
            if (word not in common_words and next_word not in common_words and
                word not in appointment_reasons and next_word not in appointment_reasons):
                return f"{word} {next_word}"

    # Pattern 3: Single capitalized word at start (e.g., "John")
    first_word = text.split()[0] if text else ""
    if first_word and first_word[0].isupper():
        first_word_clean = first_word.rstrip(",.:;!?")
        common_starts = ["I", "The", "Can", "What", "When", "Yes", "No", "Sure", "OK", "I'd", "I've", "Tomorrow", "Today",
                        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
                        "Great", "Good", "Thanks", "Please", "Could", "Would", "Should", "That's", "Sounds",
                        "Hello", "Hi", "Hey", "Okay", "Actually", "Well", "So", "If", "My", "Your", "Our",
                        "Regular", "Emergency", "Cleaning", "Checkup", "Exam", "Whitening", "Root", "Filling", "Extraction"]
        if first_word_clean not in common_starts and len(first_word_clean) > 2:
            return first_word_clean

    return None

def extract_date(text: str) -> Optional[str]:
    """Extract date references from text."""
    if not text:
        return None

    text_lower = text.lower()

    # Don't extract "my appointment" or similar metadata
    if "my appointment" in text_lower or "the one" in text_lower:
        return None

    # Natural language dates
    if "tomorrow" in text_lower:
        return "tomorrow"
    if "today" in text_lower:
        return "today"
    if "next" in text_lower:
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            if day in text_lower:
                return f"next {day}"
    if any(day in text_lower for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            if day in text_lower:
                return day

    # Map written numbers to digits
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    # "in X days/weeks" or "X days/weeks from now" (both digit and word formats)
    days_match = re.search(r"in\s+(\d+)\s+days?", text_lower)
    if days_match:
        return f"in {days_match.group(1)} days"

    # "X days/weeks from now" pattern (digit format)
    from_match = re.search(r"(\d+)\s+days?\s+from\s+now", text_lower)
    if from_match:
        return f"in {from_match.group(1)} days"

    weeks_match = re.search(r"in\s+(\d+)\s+weeks?", text_lower)
    if weeks_match:
        return f"in {weeks_match.group(1)} weeks"

    # "X weeks from now" pattern (digit format)
    weeks_from_match = re.search(r"(\d+)\s+weeks?\s+from\s+now", text_lower)
    if weeks_from_match:
        return f"in {weeks_from_match.group(1)} weeks"

    # "Word_number weeks/days from now" pattern (e.g., "Two weeks from now")
    for word, num in word_to_num.items():
        if f"{word} weeks from now" in text_lower:
            return f"in {num} weeks"
        if f"{word} week from now" in text_lower:
            return f"in {num} week"
        if f"{word} days from now" in text_lower:
            return f"in {num} days"
        if f"{word} day from now" in text_lower:
            return f"in {num} day"

    # Month/day patterns
    date_match = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})", text, re.IGNORECASE)
    if date_match:
        return f"{date_match.group(1)} {date_match.group(2)}"

    return None

def extract_time(text: str) -> Optional[str]:
    """Extract time from text."""
    if not text:
        return None

    text_lower = text.lower()

    # Time keywords
    if "morning" in text_lower:
        return "morning"
    if "afternoon" in text_lower:
        return "afternoon"
    if "evening" in text_lower:
        return "evening"

    # Time patterns: "2 PM", "14:00", "2:30 PM"
    time_match = re.search(r"(\d{1,2}):?(\d{0,2})\s*(am|pm|a\.m\.|p\.m\.)?", text, re.IGNORECASE)
    if time_match:
        hour = time_match.group(1)
        minute = time_match.group(2) or "00"
        period = time_match.group(3) or ""
        return f"{hour}:{minute} {period}".strip()

    return None

def extract_reason(text: str) -> Optional[str]:
    """Extract appointment reason/type from text."""
    if not text:
        return None

    text_lower = text.lower()

    reasons = ["cleaning", "checkup", "exam", "whitening", "emergency", "root canal", "filling", "extraction"]
    for reason in reasons:
        if reason in text_lower:
            return reason

    return None

def extract_slots_for_intent(intent: str, text: str, conversation_history: list) -> Dict[str, Any]:
    """Extract slots based on intent type."""

    # Build full context from recent USER turns only (not assistant messages)
    user_turns = [turn.get("content", "") for turn in conversation_history if turn.get("role") == "user"]
    context = " ".join(user_turns[-3:])  # Last 3 user messages
    full_text = context + " " + text

    if intent == "book_appointment":
        return {
            "name": extract_name(full_text),
            "date": extract_date(full_text),
            "time": extract_time(full_text),
            "reason": extract_reason(full_text),
        }

    elif intent == "cancel_appointment":
        return {
            "name": extract_name(full_text),
            "appointment_id_or_date": extract_date(full_text) or extract_name(full_text),
        }

    elif intent == "reschedule":
        # For reschedule, use LLM-based extraction since the logic is complex
        # (need to distinguish current appointment from new appointment)
        # For now, just extract available slots and let LLM help
        return {
            "name": extract_name(full_text),
            "appointment_id_or_date": extract_date(full_text) if "my" in full_text.lower() or "current" in full_text.lower() else None,
            "new_date": extract_date(text),
            "new_time": extract_time(text),
        }

    elif intent == "insurance_question":
        return {
            "name": extract_name(full_text),
        }

    return {}
