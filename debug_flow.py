"""Debug script to trace exact flow of failing tests."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.models.state import ConversationState
from app.state_machine import state_machine
from app.services.session_manager import session_manager
from app.models.database import SessionLocal, init_db
from tests.scenarios import ALL_TEST_SCENARIOS

def debug_test_scenario(scenario_num: int):
    """Run and debug a specific scenario."""
    init_db()
    db = SessionLocal()

    # Get all tests for this scenario
    tests = [t for t in ALL_TEST_SCENARIOS if t.scenario_number == scenario_num]

    print(f"\n{'='*80}")
    print(f"DEBUGGING SCENARIO {scenario_num}: {tests[0].scenario_name if tests else 'Unknown'}")
    print(f"{'='*80}\n")

    for test in tests:
        print(f"\n{'─'*80}")
        print(f"TEST: {test.scenario_name}")
        print(f"Expected Intent: {test.expected_intent}")
        print(f"User Inputs: {test.user_inputs}")
        print(f"{'─'*80}\n")

        # Create state
        state = ConversationState(
            conversation_id="debug-test",
            call_id="DEBUG-TEST",
            phone_number="+1-555-0000",
            conversation_history=[],
            turn_count=0,
            start_time=None,
            last_update=None,
            intent=None,
            confidence=0.0,
            slots={},
            resolved=False,
            escalated=False,
            escalation_reason=None,
            clarification_count=0,
            sentiment=None,
            greeting_done=False,
        )

        # Add greeting
        state["conversation_history"].append({
            "role": "assistant",
            "content": "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?"
        })
        state["greeting_done"] = True

        # Process each user input
        for i, user_input in enumerate(test.user_inputs, 1):
            print(f"TURN {i}: USER INPUT")
            print(f"  > {user_input}\n")

            state["conversation_history"].append({
                "role": "user",
                "content": user_input
            })
            state["turn_count"] += 1

            # Run through state machine
            try:
                result = state_machine.graph.invoke(state, config={"recursion_limit": 500})
                state = result
            except Exception as e:
                print(f"  ❌ ERROR: {e}\n")
                break

            # Show state after this turn
            print(f"STATE AFTER TURN {i}:")
            print(f"  Intent: {state.get('intent')}")
            print(f"  Confidence: {state.get('confidence')}")
            print(f"  Resolved: {state.get('resolved')}")
            print(f"  Escalated: {state.get('escalated')}")
            print(f"  Escalation Reason: {state.get('escalation_reason')}")
            print(f"  Clarification Count: {state.get('clarification_count')}")
            print(f"  Slots: {state.get('slots')}")

            # Show last assistant message
            if state["conversation_history"][-1]["role"] == "assistant":
                last_msg = state["conversation_history"][-1]["content"]
                print(f"  Last System Message: {last_msg[:100]}...")

            print()

        # Final result
        print(f"FINAL RESULT:")
        print(f"  Total Turns: {state['turn_count']}")
        print(f"  Intent: {state['intent']}")
        print(f"  Resolved: {state['resolved']}")
        print(f"  Escalated: {state['escalated']}")
        print(f"  Status: {'✅ PASS' if state['resolved'] else ('⚠️  ESCALATE' if state['escalated'] else '❌ FAIL')}")
        print()

    db.close()

if __name__ == "__main__":
    scenario = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    debug_test_scenario(scenario)
