import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM integration using OpenRouter (OpenAI-compatible API)."""

    def __init__(self):
        logger.info("📝 LLMService initialized (lazy-loaded)")
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.LLM_MODEL
        self._client = None

    def _get_client(self):
        """Lazy-load OpenAI client on first use."""
        if self._client is None:
            if not self.api_key:
                logger.warning("⚠️ OPENROUTER_API_KEY not set")
                return None
            try:
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                logger.info(f"✅ OpenRouter client created for model: {self.model}")
            except Exception as e:
                logger.error(f"❌ Failed to create OpenRouter client: {e}")
                return None
        return self._client

    @property
    def client(self):
        """Get or create the OpenAI client."""
        return self._get_client()

    def detect_intent(self, user_input: str, conversation_history: list = None, current_intent: str = None, slots: Dict = None) -> Dict[str, Any]:
        """Detect intent with structured hard rules FIRST, then LLM validation.
        ARCHITECTURAL FIX #3: Hard rules before LLM classification."""
        if not self.client:
            return {"intent": "unknown", "confidence": 0.0, "reasoning": "LLM unavailable"}

        user_lower = user_input.lower()

        # HARD RULES (100% match, no LLM needed)

        # Wrong number - exact keyword match
        wrong_number_keywords = ["wrong number", "not a dentist", "pizza", "delivery", "police", "bank", "dmv", "taxi", "uber"]
        if any(kw in user_lower for kw in wrong_number_keywords):
            print(f"✅ HARD RULE: wrong_number detected")
            return {"intent": "wrong_number", "confidence": 0.99, "reasoning": "Hard rule: wrong number keyword"}

        # Escalation requests - exact keyword match
        escalate_keywords = ["talk to human", "speak to agent", "speak to someone", "real person", "representative", "manager", "supervisor"]
        if any(kw in user_lower for kw in escalate_keywords):
            print(f"✅ HARD RULE: escalate_human detected")
            return {"intent": "escalate_human", "confidence": 0.99, "reasoning": "Hard rule: escalation request"}

        # Hours/location questions - exact keyword match
        hours_keywords = ["hours", "when are you open", "location", "address", "where are you", "open today", "open now", "what time"]
        if any(kw in user_lower for kw in hours_keywords):
            print(f"✅ HARD RULE: hours_location detected")
            return {"intent": "hours_location", "confidence": 0.99, "reasoning": "Hard rule: hours/location question"}

        # Insurance questions - EXTENDED keyword list (ARCHITECTURAL FIX #3)
        insurance_keywords = ["insurance", "accept insurance", "coverage", "plan", "deductible", "copay", "billing",
                             "which insurance", "do you accept", "network", "provider", "in-network", "out-of-network",
                             "charged", "bill", "payment", "cost"]
        if any(kw in user_lower for kw in insurance_keywords):
            print(f"✅ HARD RULE: insurance_question detected")
            return {"intent": "insurance_question", "confidence": 0.99, "reasoning": "Hard rule: insurance keyword"}

        # LEVEL 2: Multi-turn context awareness
        if current_intent and current_intent != "unknown":
            if current_intent == "book_appointment":
                if any(word in user_lower for word in ["cancel", "reschedule", "change", "different day"]):
                    return {"intent": "cancel_appointment", "confidence": 0.8, "reasoning": "User switched to cancellation"}
                else:
                    return {"intent": "book_appointment", "confidence": 0.85, "reasoning": "Continuing appointment booking"}

            elif current_intent == "cancel_appointment":
                return {"intent": "cancel_appointment", "confidence": 0.85, "reasoning": "Providing cancellation details"}

            elif current_intent == "reschedule":
                return {"intent": "reschedule", "confidence": 0.85, "reasoning": "Providing reschedule details"}

        # LEVEL 3: LLM for ambiguous cases
        prompt = f"""Classify this user message into ONE of these intents:
- book_appointment: Wants to schedule a new appointment
- cancel_appointment: Wants to cancel an existing appointment
- reschedule: Wants to change appointment date/time
- insurance_question: Question about insurance or billing
- hours_location: Question about clinic hours or location
- escalate_human: Explicit request for a human agent
- wrong_number: Call is misdirected
- unknown: Cannot determine intent

User message: "{user_input}"
Current conversation intent: {current_intent if current_intent else "None"}

Respond ONLY with valid JSON:
{{"intent": "<one of the intents above>", "confidence": <0.0 to 1.0>, "reasoning": "<brief reason>"}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
            )

            response_text = response.choices[0].message.content
            result = json.loads(response_text)

            # Ensure minimum confidence
            if result["confidence"] < 0.5:
                result["intent"] = "unknown"

            return result
        except Exception as e:
            logger.error(f"❌ LLM error: {e}")
            return {"intent": "unknown", "confidence": 0.0, "reasoning": f"Error: {str(e)}"}

    def extract_slots(
        self, intent: str, user_input: str, current_slots: Dict[str, str], conversation_history: list = None
    ) -> Dict[str, Any]:
        """Extract slots needed for the detected intent."""
        if not self.client:
            return {
                "extracted_slots": {},
                "all_slots_filled": False,
                "next_question": "I'm having trouble processing your request.",
            }

        required_slots = {
            "book_appointment": ["name", "date", "time", "reason"],
            "cancel_appointment": ["name", "appointment_id_or_date"],
            "reschedule": ["name", "appointment_id_or_date", "new_date", "new_time"],
            "insurance_question": ["name"],
            "hours_location": [],
            "escalate_human": [],
            "wrong_number": [],
            "unknown": [],
        }

        slots_needed = required_slots.get(intent, [])
        missing_slots = [s for s in slots_needed if s not in current_slots or not current_slots[s]]

        # Build conversation context for better extraction
        history_context = ""
        if conversation_history:
            history_context = "Conversation so far:\n"
            for turn in conversation_history[-6:]:  # Include more context for reschedule scenarios
                content = turn['content'][:70] + "..." if len(turn['content']) > 70 else turn['content']
                history_context += f"- {turn['role']}: {content}\n"

        # Build clear slot definitions based on intent
        slot_definitions = ""
        if intent == "reschedule":
            slot_definitions = """
SLOT DEFINITIONS (RESCHEDULE) - CRITICAL:
- name: Patient's full name (e.g., "John Smith")
- appointment_id_or_date: CURRENT appointment to reschedule FROM
  * Extract from: "my appointment", "my 2pm appointment", "the one on Tuesday", "next Friday's appointment"
  * Look for: references to their EXISTING appointment (use any date/time mentioned in context)
  * Examples: "my appointment", "Tuesday at 2pm", "the one I have", "current appointment"
- new_date: NEW appointment date they want (e.g., "tomorrow", "next Monday", "Sept 15")
- new_time: NEW appointment time they want (e.g., "10 AM", "2:30 PM", "morning")

CRITICAL RULE: Do NOT confuse current appointment with new appointment!
- If user says "reschedule my appointment to tomorrow", extract:
  * appointment_id_or_date = "my appointment" (or whatever they said about current)
  * new_date = "tomorrow"
"""
        elif intent == "book_appointment":
            slot_definitions = """
SLOT DEFINITIONS (BOOKING):
- name: Patient's full name
- date: Desired appointment date (e.g., "tomorrow", "next Monday", "Sept 15")
- time: Desired appointment time (e.g., "10 AM", "2:30 PM", "afternoon")
- reason: Type of appointment (e.g., "cleaning", "checkup", "whitening", "emergency")
"""
        elif intent == "cancel_appointment":
            slot_definitions = """
SLOT DEFINITIONS (CANCELLATION):
- name: Patient's full name
- appointment_id_or_date: Which appointment to cancel (e.g., "my 2pm", "Tuesday's", "next week's")
"""

        prompt = f"""You are helping a dental clinic receptionist collect appointment information.

{slot_definitions}
Conversation so far:
{history_context}

Currently filled: {current_slots if current_slots else 'nothing yet'}
Still need: {missing_slots}

User just said: "{user_input}"

EXTRACTION RULES:
1. Extract ONLY the missing slots from user's message
2. Names: Accept partial (first name only is fine)
3. Dates: Accept natural language ("tomorrow", "next Monday", "Sept 15", "same day")
4. Times: Accept natural language ("10 AM", "afternoon", "evening")
5. For reschedule: Do NOT mix up current vs new appointment dates!
   - appointment_id_or_date = the appointment they want to CHANGE FROM
   - new_date/new_time = the appointment they want to CHANGE TO

SPECIAL RULES FOR RESCHEDULE:
- If user says "reschedule my appointment" or "I want to reschedule", extract appointment_id_or_date="my appointment"
- If user says "my 2pm appointment" or "Tuesday's appointment", extract that as appointment_id_or_date
- Only extract new_date/new_time when user explicitly says "TO [date]" or "at [time]"
- If user provides date/time in response to "which appointment", check context to see if it's the current or new appointment

If ALL required slots now have values, set all_slots_filled=true and ask for confirmation.
If slots still missing, ask for ONE specific missing piece.

Respond with ONLY valid JSON:
{{
    "extracted_slots": {{"<slot>": "<extracted_value or null>"}},
    "all_slots_filled": <true ONLY if all required slots now have non-null values>,
    "next_question": "<natural follow-up question or confirmation>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )

            response_text = response.choices[0].message.content
            result = json.loads(response_text)

            # VALIDATE AND NORMALIZE slots using date_parser
            from app.utils.date_parser import parse_natural_date, parse_natural_time

            if "date" in result["extracted_slots"] and result["extracted_slots"]["date"]:
                parsed_date = parse_natural_date(result["extracted_slots"]["date"])
                if parsed_date:
                    result["extracted_slots"]["date"] = parsed_date

            if "time" in result["extracted_slots"] and result["extracted_slots"]["time"]:
                parsed_time = parse_natural_time(result["extracted_slots"]["time"])
                if parsed_time:
                    result["extracted_slots"]["time"] = parsed_time

            if "new_date" in result["extracted_slots"] and result["extracted_slots"]["new_date"]:
                parsed_date = parse_natural_date(result["extracted_slots"]["new_date"])
                if parsed_date:
                    result["extracted_slots"]["new_date"] = parsed_date

            if "new_time" in result["extracted_slots"] and result["extracted_slots"]["new_time"]:
                parsed_time = parse_natural_time(result["extracted_slots"]["new_time"])
                if parsed_time:
                    result["extracted_slots"]["new_time"] = parsed_time

            logger.debug(f"📝 Slots extracted: {result['extracted_slots']}")
            return result
        except Exception as e:
            logger.error(f"❌ Slot extraction error: {e}")
            return {
                "extracted_slots": {},
                "all_slots_filled": False,
                "next_question": "Could you please repeat that?",
            }

    def generate_confirmation(self, intent: str, slots: Dict[str, str]) -> str:
        """Generate a confirmation message based on slots."""
        if not self.client:
            return "Can you confirm these details are correct?"

        prompt = f"""Generate a natural, friendly confirmation message for a {intent} request with these details:
{json.dumps(slots, indent=2)}

Keep it concise (1-2 sentences) and ask the user to confirm if correct.
Respond with ONLY the message (no JSON, no markdown)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Confirmation generation error: {e}")
            return "Is this correct?"

    def generate_response(self, context: str) -> str:
        """Generate a natural response for the given context."""
        if not self.client:
            return "How can I help you?"

        prompt = f"""Respond naturally and helpfully to this context:
{context}

Keep responses concise and friendly. Respond with ONLY the message (no JSON, no markdown)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            return "How can I help you?"

    def detect_sentiment(self, user_input: str) -> Dict[str, Any]:
        """Detect sentiment from user input."""
        if not self.client:
            return {"sentiment": "neutral", "score": 0.0, "reason": "Unable to analyze"}

        prompt = f"""Analyze the sentiment of this user input:
"{user_input}"

Respond with ONLY valid JSON (no markdown):
{{
    "sentiment": "<positive|neutral|negative|angry>",
    "score": <-1.0 to 1.0>,
    "reason": "<brief explanation>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150,
            )

            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            return result
        except Exception as e:
            logger.error(f"❌ Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.0, "reason": "Parse error"}

    def classify_confirmation(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Classify if user confirmed, rejected, or is unclear about details."""
        if not self.client:
            return {"response_type": "unclear", "confidence": 0.0}

        prompt = f"""The user is responding to a confirmation request.

Context: {context}
User response: "{user_input}"

Is this a YES (confirm/agree), NO (reject/change), or UNCLEAR (needs clarification)?

Respond with ONLY valid JSON:
{{
    "response_type": "<yes|no|unclear>",
    "confidence": <0.0 to 1.0>,
    "reasoning": "<brief explanation>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=150,
            )

            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            logger.error(f"❌ Confirmation classification error: {e}")
            return {"response_type": "unclear", "confidence": 0.0}
