"""
Test Runner for 50 Dental Clinic AI Agent Scenarios
Executes all test conversations and collects metrics
"""

import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.state import ConversationState, Turn
from app.state_machine import state_machine
from app.services.session_manager import session_manager
from app.services.appointment_service import AppointmentService
from app.models.database import SessionLocal, init_db
from tests.scenarios import ALL_TEST_SCENARIOS, SCENARIO_NAMES


class TestMetrics:
    """Track metrics across test runs."""

    def __init__(self):
        self.total_tests = 0
        self.resolved = 0
        self.escalated = 0
        self.failed = 0
        self.intent_accuracy = 0
        self.correct_intents = 0
        self.turns_data = []
        self.results = []

    def add_result(self, test_name: str, scenario_num: int, expected_intent: str,
                   actual_intent: str, resolved: bool, escalated: bool, turns: int):
        """Record test result."""
        self.total_tests += 1

        if resolved:
            self.resolved += 1
        elif escalated:
            self.escalated += 1
        else:
            self.failed += 1

        if actual_intent == expected_intent:
            self.correct_intents += 1

        self.turns_data.append(turns)

        self.results.append({
            "test_num": self.total_tests,
            "scenario": scenario_num,
            "name": test_name,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "resolved": resolved,
            "escalated": escalated,
            "turns": turns,
            "status": "✅" if resolved else ("⚠️" if escalated else "❌"),
        })

    def get_summary(self) -> Dict:
        """Calculate final metrics."""
        if self.total_tests == 0:
            return {}

        avg_turns = sum(self.turns_data) / len(self.turns_data) if self.turns_data else 0
        self.intent_accuracy = (self.correct_intents / self.total_tests * 100) if self.total_tests > 0 else 0

        return {
            "total_tests": self.total_tests,
            "resolved_count": self.resolved,
            "escalated_count": self.escalated,
            "failed_count": self.failed,
            "resolution_rate": (self.resolved / self.total_tests * 100) if self.total_tests > 0 else 0,
            "escalation_rate": (self.escalated / self.total_tests * 100) if self.total_tests > 0 else 0,
            "avg_turns_to_resolution": avg_turns,
            "intent_accuracy": self.intent_accuracy,
            "correct_intents": self.correct_intents,
        }

    def print_results_table(self):
        """Print results in table format."""
        print("\n" + "=" * 140)
        print("TEST RESULTS - ALL 50 SCENARIOS")
        print("=" * 140)
        print(f"{'#':<4} {'Scenario':<3} {'Test Name':<40} {'Expected Intent':<20} {'Actual Intent':<20} {'Result':<10} {'Turns':<6}")
        print("-" * 140)

        for result in self.results:
            actual = result['actual_intent'] or "error"
            print(f"{result['test_num']:<4} {result['scenario']:<3} {result['name']:<40} {result['expected_intent']:<20} {actual:<20} {result['status']:<10} {result['turns']:<6}")

        print("=" * 140)

    def print_summary(self):
        """Print summary statistics."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("METRICS SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run:              {summary.get('total_tests', 0)}")
        print(f"✅ Resolved (no escalation):  {summary.get('resolved_count', 0)} ({summary.get('resolution_rate', 0):.1f}%)")
        print(f"⚠️  Escalated to Human:       {summary.get('escalated_count', 0)} ({summary.get('escalation_rate', 0):.1f}%)")
        print(f"❌ Failed:                    {summary.get('failed_count', 0)}")
        print(f"📊 Avg Turns to Resolution:  {summary.get('avg_turns_to_resolution', 0):.2f}")
        print(f"🎯 Intent Classification:    {summary.get('correct_intents', 0)}/{summary.get('total_tests', 0)} ({summary.get('intent_accuracy', 0):.1f}%)")
        print("=" * 60 + "\n")

        return summary


def run_test_scenario(scenario, metrics: TestMetrics):
    """Run a single test scenario - Process messages sequentially without restarting graph."""
    # Initialize database
    init_db()
    db = SessionLocal()

    # Create conversation state
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
        collected_slots={},  # ARCHITECTURAL FIX #2
        missing_slots=[],  # ARCHITECTURAL FIX #2
        resolved=False,
        escalated=False,
        escalation_reason=None,
        clarification_count=0,
        sentiment=None,
        consecutive_negative_sentiments=0,
        greeting_done=False,
        confirmation_sent=False,
    )

    # Add greeting to history
    state["conversation_history"].append({
        "role": "assistant",
        "content": "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?"
    })
    state["greeting_done"] = True  # Mark greeting as done

    # FIXED APPROACH: Process each message, but increase recursion limit significantly
    # to allow slot-filling loops to complete naturally
    for user_input in scenario.user_inputs:
        # Add user message
        state["conversation_history"].append({
            "role": "user",
            "content": user_input
        })
        state["turn_count"] += 1

        # Run through state machine with MUCH higher recursion limit
        # This allows slot-filling to loop and complete without hitting limit
        try:
            result = state_machine.graph.invoke(state, config={"recursion_limit": 500})
            state = result
        except Exception as e:
            print(f"    ❌ Error in state machine: {e}")
            break

    # Record result
    metrics.add_result(
        test_name=scenario.scenario_name,
        scenario_num=scenario.scenario_number,
        expected_intent=scenario.expected_intent,
        actual_intent=state.get("intent", "unknown"),
        resolved=state.get("resolved", False),
        escalated=state.get("escalated", False),
        turns=state.get("turn_count", 0)
    )

    # Cleanup
    session_manager.delete_state(call_id)
    db.close()


def run_all_tests():
    """Run all 50 test scenarios."""
    print("🧪 Dental Clinic AI Agent - Test Suite")
    print("=" * 60)
    print(f"Running {len(ALL_TEST_SCENARIOS)} test scenarios...")
    print("=" * 60 + "\n")

    metrics = TestMetrics()

    # Run tests
    for i, scenario in enumerate(ALL_TEST_SCENARIOS, 1):
        try:
            print(f"[{i:2d}/50] Running: {scenario.scenario_name}...", end=" ")
            run_test_scenario(scenario, metrics)
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")
            metrics.add_result(
                scenario.scenario_name,
                scenario.scenario_number,
                scenario.expected_intent,
                "error",
                False,
                False,
                0
            )

    # Print results
    metrics.print_results_table()
    summary = metrics.print_summary()

    # Save results to JSON
    output_file = Path(__file__).parent.parent / "test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "results": metrics.results,
        }, f, indent=2)

    print(f"📊 Results saved to: {output_file}")

    return summary


def run_scenario_group(scenario_num: int):
    """Run all tests for a specific scenario (by number 1-10)."""
    print(f"🧪 Running Scenario {scenario_num}: {SCENARIO_NAMES[scenario_num - 1]}")
    print("=" * 60 + "\n")

    metrics = TestMetrics()
    scenario_tests = [t for t in ALL_TEST_SCENARIOS if t.scenario_number == scenario_num]

    for scenario in scenario_tests:
        try:
            print(f"  {scenario.scenario_name}...", end=" ")
            run_test_scenario(scenario, metrics)
            print("✅")
        except Exception as e:
            print(f"❌ {e}")

    metrics.print_results_table()
    metrics.print_summary()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific scenario by number (1-10)
        try:
            scenario_num = int(sys.argv[1])
            if 1 <= scenario_num <= 10:
                run_scenario_group(scenario_num)
            else:
                print("Invalid scenario number. Use 1-10.")
        except ValueError:
            print("Invalid argument. Usage: python test_runner.py [scenario_number]")
    else:
        # Run all tests
        run_all_tests()
