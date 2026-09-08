"""
50 Test Scenarios for Dental Clinic AI Agent
10 scenarios × 5 variations each
"""

from dataclasses import dataclass
from typing import List


@dataclass
class TestScenario:
    scenario_number: int
    scenario_name: str
    description: str
    user_inputs: List[str]
    expected_intent: str
    should_resolve: bool
    should_escalate: bool


# ==================== SCENARIO 1: New Appointment Booking ====================

SCENARIO_1_TESTS = [
    TestScenario(
        scenario_number=1,
        scenario_name="Book Appointment - Cleaning",
        description="User wants to book a regular cleaning appointment",
        user_inputs=[
            "I need to schedule a cleaning",
            "My name is John Smith",
            "Next Friday at 2 PM",
            "yes",
        ],
        expected_intent="book_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=1,
        scenario_name="Book Appointment - Whitening",
        description="User wants to book teeth whitening",
        user_inputs=[
            "Can I book a teeth whitening appointment?",
            "Sarah Johnson",
            "Next Tuesday at 10 AM",
            "yes",
        ],
        expected_intent="book_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=1,
        scenario_name="Book Appointment - Emergency",
        description="User needs emergency dental care",
        user_inputs=[
            "I have a severe toothache, can I come in today?",
            "Michael Brown",
            "Today at 3 PM",
            "yes, that works",
        ],
        expected_intent="book_appointment",
        should_resolve=False,  # Emergency same-day may fail validation
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=1,
        scenario_name="Book Appointment - Exam",
        description="User wants dental exam",
        user_inputs=[
            "I'd like to schedule a dental exam",
            "Emily Davis",
            "Next Saturday at 10 AM",
            "sounds good",
        ],
        expected_intent="book_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=1,
        scenario_name="Book Appointment - Unclear Initial",
        description="User is vague initially about appointment type",
        user_inputs=[
            "I need to see a dentist",
            "Robert Wilson",
            "What reasons can I schedule for?",
            "Regular checkup",
            "Two weeks from now at 2 PM",
            "yes",
        ],
        expected_intent="book_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 2: Cancellation ====================

SCENARIO_2_TESTS = [
    TestScenario(
        scenario_number=2,
        scenario_name="Cancel Appointment - Found by Name",
        description="User cancels upcoming appointment",
        user_inputs=[
            "I need to cancel my appointment",
            "Jennifer Garcia",
            "yes, cancel it",
        ],
        expected_intent="cancel_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=2,
        scenario_name="Cancel Appointment - Confirm Details",
        description="User cancels after confirming details",
        user_inputs=[
            "Cancel my appointment",
            "David Martinez",
            "Next week",
            "that's the one",
        ],
        expected_intent="cancel_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=2,
        scenario_name="Cancel Appointment - No Upcoming",
        description="User has no upcoming appointments",
        user_inputs=[
            "I want to cancel",
            "Lisa Anderson",
            "I had one last week",
        ],
        expected_intent="cancel_appointment",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=2,
        scenario_name="Cancel Appointment - Already Cancelled",
        description="User tries to cancel already-cancelled appointment",
        user_inputs=[
            "Please cancel my appointment",
            "James Taylor",
            "The one I mentioned",
        ],
        expected_intent="cancel_appointment",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=2,
        scenario_name="Cancel Appointment - Unclear Name",
        description="Agent needs clarification on patient name",
        user_inputs=[
            "I want to cancel",
            "Um, my name is M... uh, Maria... Maria Thomas",
            "yes, that's me",
        ],
        expected_intent="cancel_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 3: Rescheduling ====================

SCENARIO_3_TESTS = [
    TestScenario(
        scenario_number=3,
        scenario_name="Reschedule - Move to Earlier",
        description="User wants to move appointment to earlier time",
        user_inputs=[
            "Can I reschedule my appointment to earlier?",
            "John Smith",
            "Tomorrow at 9 AM",
            "yes, that's perfect",
        ],
        expected_intent="reschedule",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=3,
        scenario_name="Reschedule - Move to Later",
        description="User needs to move appointment to later date",
        user_inputs=[
            "I need to reschedule",
            "Sarah Johnson",
            "Three weeks from now",
            "confirm",
        ],
        expected_intent="reschedule",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=3,
        scenario_name="Reschedule - Unavailable Time",
        description="New time slot requested is unavailable",
        user_inputs=[
            "Reschedule my appointment",
            "Michael Brown",
            "Same day but 2:30 PM",
            "yes",
        ],
        expected_intent="reschedule",
        should_resolve=False,  # May fail if slot taken
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=3,
        scenario_name="Reschedule - Weekend",
        description="User wants weekend appointment",
        user_inputs=[
            "Can I reschedule to Saturday?",
            "Emily Davis",
            "Next Saturday at 10 AM",
            "that works for me",
        ],
        expected_intent="reschedule",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=3,
        scenario_name="Reschedule - Multiple Changes",
        description="User changes mind about new time",
        user_inputs=[
            "I want to reschedule",
            "Robert Wilson",
            "Wait, can we do 11 AM instead of 2 PM?",
            "yes, 11 AM is better",
        ],
        expected_intent="reschedule",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 4: Insurance Question ====================

SCENARIO_4_TESTS = [
    TestScenario(
        scenario_number=4,
        scenario_name="Insurance - General Question",
        description="User asks about insurance coverage",
        user_inputs=[
            "Do you accept insurance?",
            "Jennifer Garcia",
        ],
        expected_intent="insurance_question",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=4,
        scenario_name="Insurance - Specific Provider",
        description="User asks about specific insurance",
        user_inputs=[
            "Hi, do you take Blue Cross?",
            "David Martinez",
        ],
        expected_intent="insurance_question",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=4,
        scenario_name="Insurance - Coverage Details",
        description="User wants detailed coverage info",
        user_inputs=[
            "What's covered for cleanings with my insurance?",
            "Lisa Anderson",
        ],
        expected_intent="insurance_question",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=4,
        scenario_name="Insurance - Multiple Providers",
        description="User asks about multiple providers",
        user_inputs=[
            "Do you take Delta or United Healthcare?",
            "James Taylor",
        ],
        expected_intent="insurance_question",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=4,
        scenario_name="Insurance - Billing Question",
        description="User has billing-related insurance question",
        user_inputs=[
            "I'm calling about my bill from last visit. Do you bill insurance directly?",
            "Maria Thomas",
        ],
        expected_intent="insurance_question",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 5: Hours & Location ====================

SCENARIO_5_TESTS = [
    TestScenario(
        scenario_number=5,
        scenario_name="Hours - General Question",
        description="User asks when clinic is open",
        user_inputs=[
            "What are your hours?",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=5,
        scenario_name="Hours - Location Question",
        description="User asks for address",
        user_inputs=[
            "Where are you located?",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=5,
        scenario_name="Hours - Weekend Availability",
        description="User asks about weekend hours",
        user_inputs=[
            "Are you open on Saturday?",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=5,
        scenario_name="Hours - Both Hours and Location",
        description="User asks for hours and address",
        user_inputs=[
            "Can you tell me your hours and address?",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=5,
        scenario_name="Hours - After-Hours Call",
        description="User calls outside of business hours",
        user_inputs=[
            "Hi, are you open right now? It's 11 PM",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 6: After-Hours Call ====================

SCENARIO_6_TESTS = [
    TestScenario(
        scenario_number=6,
        scenario_name="After-Hours - Late Night",
        description="User calls late at night",
        user_inputs=[
            "Hello? Anyone there? It's 11:30 PM",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=6,
        scenario_name="After-Hours - Early Morning",
        description="User calls very early morning",
        user_inputs=[
            "Hi, calling at 6 AM. Can I make an appointment?",
        ],
        expected_intent="book_appointment",
        should_resolve=False,  # Outside hours
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=6,
        scenario_name="After-Hours - Emergency",
        description="User has dental emergency after hours",
        user_inputs=[
            "It's 2 AM and I have terrible pain. I need help!",
        ],
        expected_intent="book_appointment",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=6,
        scenario_name="After-Hours - Asks Hours",
        description="User calls after-hours asking for hours",
        user_inputs=[
            "We're closed, but what time do you open tomorrow?",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=6,
        scenario_name="After-Hours - Sunday",
        description="User calls on Sunday (closed)",
        user_inputs=[
            "Hi, it's Sunday. When do you open on Monday?",
        ],
        expected_intent="hours_location",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 7: Angry Caller ====================

SCENARIO_7_TESTS = [
    TestScenario(
        scenario_number=7,
        scenario_name="Angry - Missed Appointment",
        description="Upset about missing appointment",
        user_inputs=[
            "I CANNOT BELIEVE I missed my appointment! This is ridiculous!",
            "What are my options?",
        ],
        expected_intent="book_appointment",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=7,
        scenario_name="Angry - Billing Issue",
        description="Frustrated with billing",
        user_inputs=[
            "You people charged me TWICE! This is unacceptable!",
        ],
        expected_intent="unknown",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=7,
        scenario_name="Angry - Service Complaint",
        description="Unhappy with previous visit",
        user_inputs=[
            "Your dentist was rude and the service was terrible!",
            "I want to speak to a manager!",
        ],
        expected_intent="escalate_human",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=7,
        scenario_name="Angry - Long Wait",
        description="Frustrated about wait time",
        user_inputs=[
            "I waited 45 minutes last time! I'm NOT coming back unless you fix this!",
        ],
        expected_intent="unknown",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=7,
        scenario_name="Angry - Then Calms Down",
        description="Starts angry but then cooperates",
        user_inputs=[
            "This is ridiculous! I need to reschedule and it better be convenient!",
            "John Doe",
            "Next Tuesday at 10 AM",
            "fine, that works",
        ],
        expected_intent="reschedule",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 8: Unclear Request ====================

SCENARIO_8_TESTS = [
    TestScenario(
        scenario_number=8,
        scenario_name="Unclear - Mumbled Audio",
        description="User input is hard to understand",
        user_inputs=[
            "Uh, I need... mmm... something about my, uh... appointment?",
            "Can you speak clearly please?",
            "I need to schedule an appointment",
        ],
        expected_intent="book_appointment",
        should_resolve=False,  # Needs clarification
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=8,
        scenario_name="Unclear - Multiple Topics",
        description="User talks about multiple things",
        user_inputs=[
            "Hi, I want to book an appointment but also I'm wondering about insurance and maybe cancel something?",
        ],
        expected_intent="unknown",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=8,
        scenario_name="Unclear - Contradictory Info",
        description="User gives contradictory information",
        user_inputs=[
            "I want to reschedule for next Monday... wait, I mean cancel it entirely... no, reschedule is fine",
        ],
        expected_intent="reschedule",
        should_resolve=False,
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=8,
        scenario_name="Unclear - Vague Time",
        description="User gives unclear time preference",
        user_inputs=[
            "I want an appointment soon-ish maybe afternoon or morning I'm not sure",
            "OK I'll say Monday around 2 PM",
        ],
        expected_intent="book_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=8,
        scenario_name="Unclear - Accidental Input",
        description="User accidentally says something confusing",
        user_inputs=[
            "No wait I meant yes I think maybe",
            "Can you just confirm if I have an appointment tomorrow?",
        ],
        expected_intent="unknown",
        should_resolve=False,
        should_escalate=True,
    ),
]

# ==================== SCENARIO 9: Wrong Number ====================

SCENARIO_9_TESTS = [
    TestScenario(
        scenario_number=9,
        scenario_name="Wrong Number - Pizza Place",
        description="User thinks they called a pizza restaurant",
        user_inputs=[
            "Is this Luigi's Pizza?",
        ],
        expected_intent="wrong_number",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=9,
        scenario_name="Wrong Number - Bank",
        description="User looking for their bank",
        user_inputs=[
            "I'm trying to reach Wells Fargo. Is this the right number?",
        ],
        expected_intent="wrong_number",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=9,
        scenario_name="Wrong Number - Other Business",
        description="User looking for different business",
        user_inputs=[
            "Is this Springfield Family Clinic?",
        ],
        expected_intent="wrong_number",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=9,
        scenario_name="Wrong Number - Person",
        description="User looking for specific person",
        user_inputs=[
            "Can I speak to Bob? Is this Bob's number?",
        ],
        expected_intent="wrong_number",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=9,
        scenario_name="Wrong Number - Government Agency",
        description="User trying to reach government office",
        user_inputs=[
            "Hello, is this the DMV?",
        ],
        expected_intent="wrong_number",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== SCENARIO 10: Mid-Conversation Topic Switch ====================

SCENARIO_10_TESTS = [
    TestScenario(
        scenario_number=10,
        scenario_name="Topic Switch - Booking to Cancellation",
        description="User starts booking but changes to cancellation",
        user_inputs=[
            "I want to book an appointment",
            "Actually, wait. I need to cancel instead",
            "Yes, cancel my appointment for next week",
        ],
        expected_intent="cancel_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=10,
        scenario_name="Topic Switch - Cancellation to Rescheduling",
        description="User wants to cancel but then reschedule instead",
        user_inputs=[
            "I need to cancel my Tuesday appointment",
            "Actually, can I just move it to Wednesday instead?",
            "John Smith",
            "Wednesday at 2 PM",
        ],
        expected_intent="reschedule",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=10,
        scenario_name="Topic Switch - Appointment to Insurance",
        description="User asks about appointment then insurance",
        user_inputs=[
            "Hi, I want to book an appointment",
            "Oh wait, first do you take United Healthcare?",
            "OK yes, I want to book for next Friday",
        ],
        expected_intent="book_appointment",
        should_resolve=False,  # Complex
        should_escalate=True,
    ),
    TestScenario(
        scenario_number=10,
        scenario_name="Topic Switch - Hours to Booking",
        description="User checks hours then books",
        user_inputs=[
            "What are your hours?",
            "Great, I want to book Thursday at 10 AM",
            "Sarah Johnson",
        ],
        expected_intent="book_appointment",
        should_resolve=True,
        should_escalate=False,
    ),
    TestScenario(
        scenario_number=10,
        scenario_name="Topic Switch - Multiple Back-and-Forth",
        description="User changes mind multiple times",
        user_inputs=[
            "I want to reschedule",
            "Actually, cancel it",
            "No wait, reschedule to next Monday",
            "Emily Davis",
            "Next Monday at 3 PM",
            "yes that's right",
        ],
        expected_intent="reschedule",
        should_resolve=True,
        should_escalate=False,
    ),
]

# ==================== AGGREGATE TEST SUITE ====================

ALL_SCENARIOS = [
    SCENARIO_1_TESTS,
    SCENARIO_2_TESTS,
    SCENARIO_3_TESTS,
    SCENARIO_4_TESTS,
    SCENARIO_5_TESTS,
    SCENARIO_6_TESTS,
    SCENARIO_7_TESTS,
    SCENARIO_8_TESTS,
    SCENARIO_9_TESTS,
    SCENARIO_10_TESTS,
]

# Total: 50 test scenarios
ALL_TEST_SCENARIOS = []
for scenario_list in ALL_SCENARIOS:
    ALL_TEST_SCENARIOS.extend(scenario_list)

SCENARIO_NAMES = [
    "New Appointment Booking",
    "Cancellation Request",
    "Rescheduling Appointment",
    "Insurance Coverage Question",
    "Clinic Hours & Location",
    "After-Hours Call",
    "Angry Caller",
    "Unclear Request",
    "Wrong Number",
    "Mid-Conversation Topic Switch",
]
