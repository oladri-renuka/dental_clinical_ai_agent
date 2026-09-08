"""Parse natural language dates and times to standardized formats."""

from datetime import datetime, timedelta
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


def parse_natural_date(user_input: str) -> Optional[str]:
    """Convert 'next Friday', 'tomorrow', etc. to YYYY-MM-DD format."""
    if not user_input:
        return None

    user_input = user_input.lower().strip()
    today = datetime.now()

    # Handle "today" and "same day"
    if "today" in user_input or "same day" in user_input:
        return today.strftime("%Y-%m-%d")

    # Handle "tomorrow"
    if "tomorrow" in user_input:
        target = today + timedelta(days=1)
        return target.strftime("%Y-%m-%d")

    # Parse "next Monday", "this Friday", etc.
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(weekdays):
        if day in user_input:
            # Find next occurrence of that day
            days_ahead = (i - today.weekday()) % 7
            if "next" in user_input:
                if days_ahead == 0:
                    days_ahead = 7  # Next week if it's today
            elif "this" in user_input:
                if days_ahead <= 0:
                    days_ahead = 7  # Next week if already passed
            else:
                # Default: if day hasn't passed this week, use this week; else next week
                if days_ahead == 0:
                    days_ahead = 7

            target = today + timedelta(days=days_ahead)
            return target.strftime("%Y-%m-%d")

    # Handle "fortnight" (14 days)
    if "fortnight" in user_input:
        target = today + timedelta(days=14)
        return target.strftime("%Y-%m-%d")

    # Parse "in X days/weeks/months"
    days_match = re.search(r'in\s+(\d+)\s*days?', user_input)
    if days_match:
        days = int(days_match.group(1))
        target = today + timedelta(days=days)
        return target.strftime("%Y-%m-%d")

    weeks_match = re.search(r'in\s+(\d+)\s*weeks?', user_input)
    if weeks_match:
        weeks = int(weeks_match.group(1))
        target = today + timedelta(weeks=weeks)
        return target.strftime("%Y-%m-%d")

    # Handle "next week", "last week", "two weeks from now"
    if "next week" in user_input:
        target = today + timedelta(weeks=1)
        return target.strftime("%Y-%m-%d")

    if "last week" in user_input or "last appointment" in user_input:
        target = today - timedelta(weeks=1)
        return target.strftime("%Y-%m-%d")

    two_weeks_match = re.search(r'(\d+)\s*weeks?\s*(?:from now|out)', user_input)
    if two_weeks_match:
        weeks = int(two_weeks_match.group(1))
        target = today + timedelta(weeks=weeks)
        return target.strftime("%Y-%m-%d")

    # Handle "a month" or "4 weeks"
    if "month" in user_input or "4 weeks" in user_input or "one month" in user_input:
        target = today + timedelta(days=30)
        return target.strftime("%Y-%m-%d")

    # Try to parse as explicit date (Sept 15, 9/15, 15th, etc.)
    try:
        # Try various formats
        for fmt in ["%b %d", "%B %d", "%m/%d", "%m-%d", "%d/%m", "%d-%m"]:
            try:
                parsed = datetime.strptime(user_input.replace("st", "").replace("nd", "").replace("rd", "").replace("th", ""), fmt)
                target = today.replace(month=parsed.month, day=parsed.day)
                # If date is in the past, assume next year
                if target < today:
                    target = target.replace(year=today.year + 1)
                return target.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception:
        pass

    # Try to parse YYYY-MM-DD directly
    try:
        datetime.strptime(user_input, "%Y-%m-%d")
        return user_input
    except ValueError:
        pass

    logger.warning(f"Could not parse date: {user_input}")
    return None


def parse_natural_time(user_input: str) -> Optional[str]:
    """Convert 'morning', '2 PM', '14:00', etc. to HH:MM format."""
    if not user_input:
        return None

    user_input = user_input.lower().strip()

    # Special time keywords
    if "morning" in user_input:
        return "10:00"  # Default morning time
    if "afternoon" in user_input:
        return "14:00"  # Default afternoon time
    if "evening" in user_input or "night" in user_input:
        return "17:00"  # Default evening time

    # Parse specific times: "2 PM", "14:00", "2:30 PM", etc.
    # Match patterns like: "2 PM", "2pm", "14:00", "2:30 PM", "14:30", etc.
    time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm)?', user_input)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3)

        # Handle 12-hour to 24-hour conversion
        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0

        # Validate hour/minute
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    # Try parsing direct time formats
    try:
        for fmt in ["%H:%M", "%H%M", "%I:%M %p", "%I%M %p"]:
            try:
                parsed = datetime.strptime(user_input, fmt)
                return parsed.strftime("%H:%M")
            except ValueError:
                continue
    except Exception:
        pass

    logger.warning(f"Could not parse time: {user_input}")
    return None
