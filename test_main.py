"""Unit tests for Rock-Paper-Scissors-Plus Referee Agent.

This test suite demonstrates:
- How to unit test pure functions (tools)
- How to test state mutations
- How to test agent orchestration

Run tests:
    python -m unittest test_main.py -v

Design principle:
    Pure functions (tools) are easy to test because they have no side effects.
    We pass in mock states and verify outputs.
"""

import unittest

from main import (
    GameState,
    RefereeAgent,
    resolve_round_tool,
    update_game_state_tool,
    validate_move_tool,
)


class TestRefereeTools(unittest.TestCase):
    """Test the three game logic tools.

    Why test tools separately?
    - Pure functions are deterministic (same input = same output)
    - No mocking needed
    - Tests serve as documentation
    - Easy to run before agent tests
    """

    def test_validate_move_rejects_invalid(self) -> None:
        """Test that validate_move_tool() rejects unknown moves."""
        state = GameState()
        result = validate_move_tool("lizard", "user", state)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "unknown move")

    def test_validate_move_rejects_reused_bomb(self) -> None:
        """Test that validate_move_tool() enforces one-bomb-per-player rule."""
        state = GameState(bombs_used={"user": True, "bot": False})
        result = validate_move_tool("bomb", "user", state)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "bomb already used")

    def test_resolve_round_draws(self) -> None:
        """Test that resolve_round_tool() correctly identifies draws."""
        result = resolve_round_tool("rock", "rock")
        self.assertEqual(result["winner"], "draw")
        result = resolve_round_tool("bomb", "bomb")
        self.assertEqual(result["winner"], "draw")

    def test_update_state_scores_and_rounds(self) -> None:
        """Test that update_game_state_tool() correctly updates scores and history."""
        state = GameState()
        updated = update_game_state_tool(
            state, "rock", "scissors", "user", "rock beats scissors"
        )

        # Check round increment
        self.assertEqual(updated.round_index, 1)

        # Check score updates
        self.assertEqual(updated.user_score, 1)
        self.assertEqual(updated.bot_score, 0)

        # Check history recording
        self.assertEqual(updated.history[-1]["winner"], "user")


class TestAgentFlow(unittest.TestCase):
    """Test the RefereeAgent orchestration logic.

    These tests verify that play_round() correctly:
    - Rejects invalid input without advancing the round
    - Requires exact move matching (no fuzzy parsing)
    - Returns appropriate error messages
    """

    def test_invalid_input_wastes_round(self) -> None:
        """Test that invalid input triggers an error without consuming a round."""
        state = GameState()
        agent = RefereeAgent(state)

        response = agent.play_round("totally invalid")

        # Should NOT advance round
        self.assertEqual(agent.state.round_index, 0)

        # Should indicate an error
        self.assertIn("Invalid move", response)

        # Should NOT add to history
        self.assertEqual(agent.state.history, [])

    def test_intent_requires_exact_input(self) -> None:
        """Test that interpret_intent() does exact-match parsing (no fuzzy matching)."""
        agent = RefereeAgent(GameState())

        # Exact matches should work
        self.assertEqual(agent.interpret_intent("rock"), "rock")
        self.assertEqual(agent.interpret_intent("PAPER"), "paper")
        self.assertEqual(agent.interpret_intent("  scissors  "), "scissors")

        # Non-exact should fail
        self.assertIsNone(agent.interpret_intent("r"))  # Abbreviation
        self.assertIsNone(agent.interpret_intent("stone"))  # Typo
        self.assertIsNone(agent.interpret_intent("bomb!"))  # Special char


if __name__ == "__main__":
    unittest.main()
