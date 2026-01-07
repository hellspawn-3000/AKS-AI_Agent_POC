import unittest

from main import (
    GameState,
    RefereeAgent,
    resolve_round_tool,
    update_game_state_tool,
    validate_move_tool,
)


class TestRefereeTools(unittest.TestCase):
    def test_validate_move_rejects_invalid(self) -> None:
        state = GameState()
        result = validate_move_tool("lizard", "user", state)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "unknown move")

    def test_validate_move_rejects_reused_bomb(self) -> None:
        state = GameState(bombs_used={"user": True, "bot": False})
        result = validate_move_tool("bomb", "user", state)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "bomb already used")

    def test_resolve_round_draws(self) -> None:
        result = resolve_round_tool("rock", "rock")
        self.assertEqual(result["winner"], "draw")
        result = resolve_round_tool("bomb", "bomb")
        self.assertEqual(result["winner"], "draw")

    def test_update_state_scores_and_rounds(self) -> None:
        state = GameState()
        updated = update_game_state_tool(state, "rock", "scissors", "user", "rock beats scissors")
        self.assertEqual(updated.round_index, 1)
        self.assertEqual(updated.user_score, 1)
        self.assertEqual(updated.bot_score, 0)
        self.assertEqual(updated.history[-1]["winner"], "user")


class TestAgentFlow(unittest.TestCase):
    def test_invalid_input_wastes_round(self) -> None:
        state = GameState()
        agent = RefereeAgent(state)
        response = agent.play_round("totally invalid")
        self.assertEqual(agent.state.round_index, 0)
        self.assertIn("Invalid move", response)
        self.assertEqual(agent.state.history, [])

    def test_intent_parses_synonyms(self) -> None:
        agent = RefereeAgent(GameState())
        self.assertEqual(agent.interpret_intent("I pick stone!"), "rock")
        self.assertEqual(agent.interpret_intent("s"), "scissors")
        self.assertEqual(agent.interpret_intent("Drop the nuke"), "bomb")


if __name__ == "__main__":
    unittest.main()
