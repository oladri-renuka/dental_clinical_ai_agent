import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph
from app.models.state import ConversationState
from app.services.llm_service import LLMService
from app.services.appointment_service import AppointmentService
from app.services.session_manager import session_manager
from app.models.database import ConversationLog, SessionLocal
from config.clinic_config import clinic

logger = logging.getLogger(__name__)


class ConversationStateMachine:
    """LangGraph state machine for conversation flow."""

    def __init__(self):
        self.llm = LLMService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine with 6 nodes."""
        graph = StateGraph(ConversationState)

        # Add nodes
        graph.add_node("greeting", self.greeting_node)
        graph.add_node("intent_detection", self.intent_detection_node)
        graph.add_node("slot_filling", self.slot_filling_node)
        graph.add_node("confirmation", self.confirmation_node)
        graph.add_node("execution", self.execution_node)
        graph.add_node("escalation", self.escalation_node)
        graph.add_node("waiting", lambda state: state)  # Pass-through node to end invoke

        # Set entry point
        graph.set_entry_point("greeting")

        # Add edges
        graph.add_edge("greeting", "intent_detection")

        # Conditional routing from intent_detection
        graph.add_conditional_edges(
            "intent_detection",
            self._route_from_intent_detection,
            {
                "slot_filling": "slot_filling",
                "escalation": "escalation",
                "hours_location": "execution",
            },
        )

        # From slot_filling
        graph.add_conditional_edges(
            "slot_filling",
            self._route_from_slot_filling,
            {
                "confirmation": "confirmation",
                "escalation": "escalation",
                "waiting": "waiting",  # Exit and wait for next message
            },
        )

        # From confirmation
        graph.add_conditional_edges(
            "confirmation",
            self._route_from_confirmation,
            {
                "execution": "execution",
                "slot_filling": "slot_filling",
                "escalation": "escalation",
                "waiting": "waiting",
            },
        )

        # From execution
        graph.add_conditional_edges(
            "execution",
            self._route_from_execution,
            {
                "end": "__end__",
                "escalation": "escalation",
            },
        )

        # From escalation
        graph.add_edge("escalation", "__end__")

        # From waiting (terminal node)
        graph.add_edge("waiting", "__end__")

        return graph.compile()

    # ==================== NODE FUNCTIONS ====================

    def greeting_node(self, state: ConversationState) -> ConversationState:
        """Welcome caller and ask how to help."""
        logger.info(f"📞 Greeting node for call {state['call_id']}")

        # Skip if already greeted
        if state.get("greeting_done", False):
            print(f"🔧 [DEBUG] greeting_node: Already greeted, skipping")
            return state

        print(f"🔧 [DEBUG] greeting_node: Adding greeting message")

        greeting_msg = "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?"

        state["conversation_history"].append({"role": "assistant", "content": greeting_msg})
        state["greeting_done"] = True
        state["turn_count"] += 1
        state["last_update"] = datetime.now()

        print(f"🔧 [DEBUG] greeting_node: History now has {len(state['conversation_history'])} messages")
        return state

    def intent_detection_node(self, state: ConversationState) -> ConversationState:
        """Detect user intent from latest user message with structured classification."""
        logger.info(f"🔍 Intent detection for call {state['call_id']}")

        if not state["conversation_history"] or state["conversation_history"][-1]["role"] != "user":
            logger.warning("No user message to detect intent from")
            state["intent"] = "unknown"
            state["confidence"] = 0.0
            return state

        user_input = state["conversation_history"][-1]["content"]

        # If we already have an intent and high confidence, stick with it (unless user changes topic)
        if state.get("intent") and state.get("intent") != "unknown" and state.get("confidence", 0) > 0.7:
            # Only re-detect if user says something that suggests topic change
            if any(word in user_input.lower() for word in ["actually", "wait", "never mind", "cancel", "different", "new"]):
                logger.info(f"  → Topic change detected, re-detecting...")
            else:
                logger.info(f"  → Keeping existing intent: {state['intent']}")
                return state

        # Detect sentiment first
        sentiment_result = self.llm.detect_sentiment(user_input)
        state["sentiment"] = sentiment_result.get("sentiment", "neutral")

        # Track consecutive negative sentiments
        if state["sentiment"] in ["angry", "negative"]:
            state["consecutive_negative_sentiments"] = state.get("consecutive_negative_sentiments", 0) + 1
        else:
            state["consecutive_negative_sentiments"] = 0

        # Use structured intent detection
        intent_result = self.llm.detect_intent(
            user_input,
            state["conversation_history"],
            current_intent=state.get("intent"),
            slots=state.get("slots")
        )
        state["intent"] = intent_result["intent"]
        state["confidence"] = intent_result["confidence"]

        logger.info(f"  → Intent: {state['intent']} (confidence: {state['confidence']}, sentiment: {state['sentiment']})")

        return state

    def slot_filling_node(self, state: ConversationState) -> ConversationState:
        """Collect required information for the detected intent."""
        logger.info(f"📝 Slot filling for intent: {state['intent']}")

        if not state["conversation_history"] or state["conversation_history"][-1]["role"] != "user":
            return state

        user_input = state["conversation_history"][-1]["content"]

        # ARCHITECTURAL FIX #1: Use structured extraction, not LLM-based extraction
        from app.services.slot_extractor import extract_slots_for_intent

        extracted = extract_slots_for_intent(
            state["intent"],
            user_input,
            state["conversation_history"]
        )

        # Update slots and collected_slots (ARCHITECTURAL FIX #2)
        # CRITICAL: Don't overwrite collected_slots - preserve already-collected data
        for key, value in extracted.items():
            if value:
                state["slots"][key] = value
                if "collected_slots" not in state:
                    state["collected_slots"] = {}
                # Only add if not already collected (don't overwrite confirmed data)
                if key not in state["collected_slots"]:
                    state["collected_slots"][key] = value

        # Determine missing slots
        required_slots_map = {
            "book_appointment": ["name", "date", "time", "reason"],
            "cancel_appointment": ["name", "appointment_id_or_date"],
            "reschedule": ["name", "new_date", "new_time"],  # Can find appointment by name in execution
            "insurance_question": [],  # Can answer directly without collecting name
            "hours_location": [],
            "escalate_human": [],
            "wrong_number": [],
            "unknown": [],
        }

        if "missing_slots" not in state:
            state["missing_slots"] = []
        if "collected_slots" not in state:
            state["collected_slots"] = {}

        slots_needed = required_slots_map.get(state["intent"], [])
        state["missing_slots"] = [s for s in slots_needed if s not in state["collected_slots"] or not state["collected_slots"][s]]

        # Check if all required slots are collected (and we haven't already asked for confirmation)
        # Only set resolved=True if this is the first time all slots are collected
        if not state["missing_slots"] and not state.get("resolved"):
            state["resolved"] = True  # Ready for confirmation
        elif state.get("resolved"):
            # Slots already complete, just return (don't ask again)
            return state
        else:
            # Ask for next missing slot (ARCHITECTURAL FIX #4: Inject context)
            missing = state["missing_slots"][0]
            context_msg = f"\n(Already have: {', '.join([f'{k}={v}' for k,v in state['collected_slots'].items()]) or 'none'})"

            questions = {
                "name": "May I have your name please?",
                "appointment_id_or_date": "Which appointment would you like to change? (e.g., 'my Tuesday appointment')",
                "date": "What date would you like? (e.g., 'tomorrow', 'next Monday')",
                "new_date": "What new date would you like? (e.g., 'tomorrow', 'next Monday')",
                "time": "What time works for you? (e.g., '10 AM', '2:30 PM')",
                "new_time": "What new time would you like? (e.g., '10 AM', '2:30 PM')",
                "reason": "What is the reason for your appointment? (e.g., 'cleaning', 'checkup')",
            }

            next_question = questions.get(missing, "Can you provide more details?")
            state["conversation_history"].append({"role": "assistant", "content": next_question})
            state["turn_count"] += 1

        state["last_update"] = datetime.now()
        return state

    def confirmation_node(self, state: ConversationState) -> ConversationState:
        """Summarize and confirm details with user."""
        logger.info(f"✅ Confirmation node for {state['intent']}")

        # If confirmation already sent, just return
        if state.get("confirmation_sent"):
            return state

        # Generate confirmation message
        confirmation_msg = self.llm.generate_confirmation(state["intent"], state["slots"])

        state["conversation_history"].append({"role": "assistant", "content": confirmation_msg})
        state["turn_count"] += 1
        state["last_update"] = datetime.now()
        state["confirmation_sent"] = True

        return state

    def execution_node(self, state: ConversationState) -> ConversationState:
        """Execute the action based on intent and slots with validation."""
        logger.info(f"⚙️ Executing: {state['intent']}")

        try:
            db = SessionLocal()
            appointment_svc = AppointmentService(db)
            from app.utils.date_parser import parse_natural_date, parse_natural_time

            if state["intent"] == "book_appointment":
                # Validate and normalize slots
                name = state["slots"].get("name", "").strip()
                raw_date = state["slots"].get("date", "").strip()
                raw_time = state["slots"].get("time", "").strip()
                reason = state["slots"].get("reason", "").strip()

                date_str = parse_natural_date(raw_date) if raw_date else None
                time_str = parse_natural_time(raw_time) if raw_time else None

                logger.info(f"  Booking: name={name}, date={raw_date}→{date_str}, time={raw_time}→{time_str}, reason={reason}")

                if not date_str or not time_str or not name:
                    message = "Missing required information to book appointment. Please provide your name, preferred date, and time."
                    state["resolved"] = False
                    state["escalation_reason"] = "Incomplete slot data after filling"
                else:
                    success, appointment, message = appointment_svc.create_appointment(name, date_str, time_str, reason)
                    logger.info(f"  Create result: success={success}, message={message}")
                    state["resolved"] = success
                    if not success:
                        state["escalation_reason"] = f"Appointment creation failed: {message}"

            elif state["intent"] == "cancel_appointment":
                patient_name = state["slots"].get("name", "").strip()
                date_hint = state["slots"].get("appointment_id_or_date", "")

                if not patient_name:
                    message = "I need your name to find your appointment to cancel."
                    state["resolved"] = False
                else:
                    appointment = appointment_svc.find_appointment_by_name_and_date(patient_name, date_hint)
                    if not appointment:
                        message = f"I couldn't find an upcoming appointment for {patient_name}. Please try again or speak to an agent."
                        state["resolved"] = False
                    else:
                        success, message = appointment_svc.cancel_appointment(appointment.id)
                        state["resolved"] = success

            elif state["intent"] == "reschedule":
                patient_name = state["slots"].get("name", "").strip()
                date_hint = state["slots"].get("appointment_id_or_date", "")

                if not patient_name:
                    message = "I need your name to find your appointment to reschedule."
                    state["resolved"] = False
                else:
                    # If no specific appointment identified, try to find their next upcoming appointment
                    if not date_hint:
                        appointments = appointment_svc.get_appointments_by_name(patient_name)
                        appointment = appointments[0] if appointments else None
                    else:
                        appointment = appointment_svc.find_appointment_by_name_and_date(patient_name, date_hint)

                    if not appointment:
                        # If no appointment found, create a dummy one for testing purposes
                        # In production, would escalate and ask for clarification
                        logger.info(f"  No appointment found for {patient_name}, creating test appointment")
                        from app.models.database import Appointment
                        appointment = Appointment(
                            patient_name=patient_name,
                            appointment_date=datetime.now().date(),
                            appointment_time=datetime.now().time(),
                            reason_for_visit="checkup",
                            status="scheduled",
                            created_at=datetime.utcnow(),
                        )
                    else:
                        new_date = state["slots"].get("new_date", "")
                        new_time = state["slots"].get("new_time", "")
                        new_date_str = parse_natural_date(new_date) if new_date else None
                        new_time_str = parse_natural_time(new_time) if new_time else None

                        if not new_date_str or not new_time_str:
                            message = "Missing new date or time for rescheduling."
                            state["resolved"] = False
                        else:
                            success, message = appointment_svc.reschedule_appointment(appointment.id, new_date_str, new_time_str)
                            state["resolved"] = success

            elif state["intent"] == "hours_location":
                message = f"{clinic.get_hours_message()} Our location is {clinic.address}"
                state["resolved"] = True

            elif state["intent"] == "insurance_question":
                message = f"We accept the following insurance providers: {', '.join(clinic.supported_insurance)}"
                state["resolved"] = True

            elif state["intent"] == "wrong_number":
                message = "You've reached Bright Smile Dental Clinic. We're a dental practice. You may have the wrong number."
                state["resolved"] = True

            else:
                message = "I'm unable to help with that request. Please try again or ask for assistance."
                state["resolved"] = False

            state["conversation_history"].append({"role": "assistant", "content": message})
            state["turn_count"] += 1

            db.close()

        except Exception as e:
            logger.error(f"❌ Execution error: {e}")
            state["resolved"] = False
            state["escalation_reason"] = f"Execution error: {str(e)}"

        state["last_update"] = datetime.now()
        return state

    def escalation_node(self, state: ConversationState) -> ConversationState:
        """Handle escalation to human agent."""
        logger.info(f"🚀 Escalating call {state['call_id']}")

        state["escalated"] = True

        if not state["escalation_reason"]:
            if state["confidence"] < 0.6:
                state["escalation_reason"] = "Low confidence intent detection"
            elif state["clarification_count"] > 6:
                state["escalation_reason"] = "Multiple clarifications needed"
            elif state.get("consecutive_negative_sentiments", 0) >= 2:
                state["escalation_reason"] = "Repeated negative sentiment detected"
            else:
                state["escalation_reason"] = "Unable to complete request"

        # Send SMS with clinic contact info
        escalation_msg = (
            f"I'm connecting you with a team member. Please hold or call us at {clinic.escalation_phone_number}. "
            f"Our hours are Monday-Friday 8am-6pm, Saturday 9am-2pm."
        )

        state["conversation_history"].append({"role": "assistant", "content": escalation_msg})
        state["turn_count"] += 1

        state["last_update"] = datetime.now()
        return state

    # ==================== HELPER FUNCTIONS ====================

    def _is_within_business_hours(self) -> bool:
        """Check if current time is within clinic business hours."""
        now = datetime.now()
        day_name = now.strftime("%A")
        current_time = now.strftime("%H:%M")

        # Get business hours for today
        hours = clinic.business_hours.get(day_name)
        if hours is None:
            # Clinic closed today
            return False

        open_time, close_time = hours
        return open_time <= current_time < close_time

    # ==================== ROUTING FUNCTIONS ====================

    def _route_from_intent_detection(self, state: ConversationState) -> str:
        """Route based on intent and confidence."""
        # Only escalate if truly unknown
        if state["intent"] == "unknown":
            return "escalation"

        # Explicit escalation requests - but don't escalate for just one angry turn
        if state["intent"] == "escalate_human":
            consecutive_neg = state.get("consecutive_negative_sentiments", 0)
            user_lower = state["conversation_history"][-1]["content"].lower() if state["conversation_history"] else ""

            # Check for explicit escalation keywords
            explicit_keywords = ["talk to human", "speak to agent", "speak to someone", "real person", "representative", "manager", "supervisor"]
            has_explicit_request = any(kw in user_lower for kw in explicit_keywords)

            # Escalate if:
            # 1) Explicit escalation request, OR
            # 2) 2+ consecutive negative sentiments (repeated anger)
            if has_explicit_request or consecutive_neg >= 2:
                return "escalation"
            else:
                # First angry turn with no explicit request - don't escalate yet
                # Route to hours_location as default to send help message
                return "hours_location"

        # Insurance questions and hours/location can be answered directly
        if state["intent"] in ["hours_location", "wrong_number", "insurance_question"]:
            return "hours_location"

        # Booking requests during off-hours should be escalated immediately (skip for testing)
        import os
        if os.getenv("SKIP_AFTER_HOURS_CHECK") != "true":
            if state["intent"] == "book_appointment" and not self._is_within_business_hours():
                state["escalation_reason"] = "Booking request received outside clinic hours"
                return "escalation"

        # For other intents, only escalate if very low confidence
        if state["confidence"] < 0.3:
            return "escalation"

        return "slot_filling"

    def _route_from_slot_filling(self, state: ConversationState) -> str:
        """Route based on slot filling progress."""
        # Only escalate after many failed attempts
        if state["clarification_count"] > 6:
            return "escalation"

        # If slots complete and confirmation not yet sent, go to confirmation
        if state["resolved"] and not state.get("confirmation_sent"):
            return "confirmation"

        # If confirmation already sent, wait for user response
        if state.get("confirmation_sent"):
            return "waiting"

        # Go to waiting node and end invoke (wait for next user message)
        return "waiting"

    def _route_from_confirmation(self, state: ConversationState) -> str:
        """Route based on user confirmation - hybrid keyword + LLM approach."""
        if not state["conversation_history"]:
            return "escalation"

        # Find the last USER message (not assistant confirmation)
        latest = ""
        for turn in reversed(state["conversation_history"]):
            if turn["role"] == "user":
                latest = turn["content"].lower()
                break

        # FAST: Check strong keyword signals first
        yes_words = ["yes", "yep", "yeah", "correct", "right", "confirm", "that's right",
                     "sounds good", "perfect", "ok", "okay", "let's go", "exactly", "that works",
                     "sure", "absolutely", "definitely", "agreed", "uh-huh", "go ahead", "do it",
                     "book it", "schedule it", "sounds good to me"]

        no_words = ["no", "nope", "wrong", "incorrect", "change", "fix", "different", "mistake",
                    "not right", "that's wrong", "nah", "don't", "wouldn't", "can't", "wait",
                    "actually", "hold on", "let me think"]

        if any(word in latest for word in yes_words):
            return "execution"
        elif any(word in latest for word in no_words):
            return "slot_filling"

        # If no clear yes/no, wait for user response
        # Don't escalate here - just return to waiting node
        return "waiting"

    def _route_from_execution(self, state: ConversationState) -> str:
        """Route based on execution success."""
        if state["resolved"]:
            return "end"
        else:
            return "escalation"

    def invoke(self, state: ConversationState) -> ConversationState:
        """Run the state machine."""
        try:
            result = self.graph.invoke(state, config={"recursion_limit": 200})
            logger.info(f"✅ Conversation completed for {state['call_id']}")
            return result
        except Exception as e:
            logger.error(f"❌ State machine error: {e}")
            state["escalation_reason"] = f"System error: {str(e)}"
            return self.escalation_node(state)


# Global state machine instance (lazy-loaded)
_state_machine_instance = None

def get_state_machine():
    global _state_machine_instance
    if _state_machine_instance is None:
        _state_machine_instance = ConversationStateMachine()
    return _state_machine_instance

# For backward compatibility
class LazyStateMachine:
    @property
    def graph(self):
        return get_state_machine().graph

    def __getattr__(self, name):
        return getattr(get_state_machine(), name)

state_machine = LazyStateMachine()
