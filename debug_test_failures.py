"""
Debug script to identify which tests are failing and why.
Run this to see exact failure reasons.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from app.models.state import ConversationState
from app.state_machine import state_machine
from app.services.session_manager import session_manager
from app.models.database import SessionLocal, init_db
from tests.scenarios import ALL_TEST_SCENARIOS
import uuid


def debug_test_scenario(scenario):
    """Run a single test scenario and capture detailed debug info."""
    init_db()
    db = SessionLocal()

    conversation_id = str(uuid.uuid4())
    call_id = f"TEST-{conversation_id[:8]}"

    state = ConversationState(
        conversation_id=conversation_id,
        call_id=call_id,
        phone_number="+1-555-0000",
        conversation_history=[],
        turn_count=0,
        start_time=datetime.now(),
        last_update=datetime.now(),
        intent=None,
        confidence=0.0,
        slots={},
        resolved=False,
        escalated=False,
        escalation_reason=None,
        clarification_count=0,
        sentiment=None,
        greeting_done=False,
        needs_user_input=False,
    )

    # Add greeting
    state["conversation_history"].append({
        "role": "assistant",
        "content": "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?"
    })
    state["greeting_done"] = True

    # Process each user input
    for turn_num, user_input in enumerate(scenario.user_inputs, 1):
        state["conversation_history"].append({
            "role": "user",
            "content": user_input
        })
        state["turn_count"] += 1

        try:
            result = state_machine.graph.invoke(state, config={"recursion_limit": 200})
            state = result
        except Exception as e:
            return {
                "scenario": scenario.scenario_name,
                "expected_intent": scenario.expected_intent,
                "actual_intent": state.get("intent"),
                "status": "ERROR",
                "error": str(e),
                "turn": turn_num,
                "user_input": user_input,
                "slots": state.get("slots"),
                "confidence": state.get("confidence"),
            }

    session_manager.delete_state(call_id)
    db.close()

    # Determine result
    is_passing = False
    reason = None

    if state.get("intent") != scenario.expected_intent:
        reason = f"Intent mismatch: expected {scenario.expected_intent}, got {state.get('intent')}"
    elif scenario.should_resolve and not state.get("resolved"):
        reason = f"Should resolve but escalated: {state.get('escalation_reason')}"
    elif scenario.should_escalate and not state.get("escalated"):
        reason = "Should escalate but resolved"
    else:
        is_passing = True

    return {
        "scenario": scenario.scenario_name,
        "number": scenario.scenario_number,
        "expected_intent": scenario.expected_intent,
        "actual_intent": state.get("intent"),
        "expected_resolve": scenario.should_resolve,
        "resolved": state.get("resolved"),
        "escalated": state.get("escalated"),
        "escalation_reason": state.get("escalation_reason"),
        "confidence": round(state.get("confidence", 0), 2),
        "clarification_count": state.get("clarification_count"),
        "turns": state.get("turn_count"),
        "slots": state.get("slots"),
        "status": "PASS" if is_passing else "FAIL",
        "reason": reason,
    }


def main():
    """Run all tests and print detailed debug info."""
    print("=" * 140)
    print("DETAILED TEST FAILURE ANALYSIS")
    print("=" * 140)
    print()

    results = []
    passed = 0
    failed = 0

    for i, scenario in enumerate(ALL_TEST_SCENARIOS, 1):
        result = debug_test_scenario(scenario)
        results.append(result)

        if result["status"] == "PASS":
            passed += 1
            status_emoji = "✅"
        else:
            failed += 1
            status_emoji = "❌"

        print(f"{status_emoji} [{i:2d}] {result['scenario'][:50]:<50} | "
              f"Intent: {result['actual_intent']:<20} | "
              f"Conf: {result['confidence']:<4} | "
              f"Status: {result['status']:<4}")

        if result["status"] == "FAIL":
            print(f"     └─ REASON: {result['reason']}")
            print(f"     └─ Escalation: {result['escalation_reason']}")
            if result["slots"]:
                print(f"     └─ Slots: {result['slots']}")
            print()

    # Summary
    print("\n" + "=" * 140)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(results)}")
    print("=" * 140)

    # Group failures by type
    intent_failures = [r for r in results if r["status"] == "FAIL" and r["reason"] and "Intent mismatch" in r["reason"]]
    escalation_failures = [r for r in results if r["status"] == "FAIL" and r["reason"] and "escalated" in r["reason"].lower()]
    other_failures = [r for r in results if r["status"] == "FAIL" and r["reason"] and r not in intent_failures + escalation_failures]

    print(f"\nIntent Detection Failures ({len(intent_failures)}):")
    for r in intent_failures:
        print(f"  - {r['scenario']}: expected {r['expected_intent']}, got {r['actual_intent']}")

    print(f"\nEscalation Failures ({len(escalation_failures)}):")
    for r in escalation_failures:
        print(f"  - {r['scenario']}: {r['reason']}")
        print(f"    Reason: {r['escalation_reason']}")

    if other_failures:
        print(f"\nOther Failures ({len(other_failures)}):")
        for r in other_failures:
            print(f"  - {r['scenario']}: {r['reason']}")

    # Save detailed results
    output_file = Path(__file__).parent / "debug_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{passed/len(results)*100:.1f}%",
            },
            "results": results,
        }, f, indent=2)

    print(f"\n📊 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
