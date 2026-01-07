import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from google.adk import Agent
    from google.adk.tools import tool
except ImportError:  # Fallback for local runs without ADK installed.
    def tool(_fn=None, **_kwargs):
        def _wrap(fn):
            return fn

        return _wrap if _fn is None else _fn

    class Agent:
        def __init__(self, name: str, description: str = "") -> None:
            self.name = name
            self.description = description


VALID_MOVES = {"rock", "paper", "scissors", "bomb"}
RPS_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


@dataclass
class GameState:
    round_index: int = 0
    user_score: int = 0
    bot_score: int = 0
    bombs_used: Dict[str, bool] = field(default_factory=lambda: {"user": False, "bot": False})
    history: List[Dict[str, str]] = field(default_factory=list)


@tool(name="validate_move", description="Validate a player's move and bomb usage against game rules.")
def validate_move_tool(move: Optional[str], player: str, state: GameState) -> Dict[str, str]:
    if not move:
        return {"valid": "false", "reason": "empty input"}
    if move not in VALID_MOVES:
        return {"valid": "false", "reason": "unknown move"}
    if move == "bomb" and state.bombs_used.get(player, False):
        return {"valid": "false", "reason": "bomb already used"}
    return {"valid": "true", "reason": "ok"}


@tool(name="resolve_round", description="Resolve a round outcome given two valid moves.")
def resolve_round_tool(user_move: str, bot_move: str) -> Dict[str, str]:
    if user_move == bot_move:
        return {"winner": "draw", "explanation": "Same move."}
    if user_move == "bomb" and bot_move == "bomb":
        return {"winner": "draw", "explanation": "Bomb vs bomb is a draw."}
    if user_move == "bomb":
        return {"winner": "user", "explanation": "Bomb beats all other moves."}
    if bot_move == "bomb":
        return {"winner": "bot", "explanation": "Bomb beats all other moves."}
    if RPS_BEATS[user_move] == bot_move:
        return {"winner": "user", "explanation": f"{user_move} beats {bot_move}."}
    return {"winner": "bot", "explanation": f"{bot_move} beats {user_move}."}


@tool(name="update_game_state", description="Mutate game state with the round result.")
def update_game_state_tool(
    state: GameState,
    user_move: str,
    bot_move: str,
    winner: str,
    outcome_note: str,
) -> GameState:
    if user_move == "bomb":
        state.bombs_used["user"] = True
    if bot_move == "bomb":
        state.bombs_used["bot"] = True
    if winner == "user":
        state.user_score += 1
    elif winner == "bot":
        state.bot_score += 1
    state.history.append(
        {
            "round": str(state.round_index + 1),
            "user_move": user_move,
            "bot_move": bot_move,
            "winner": winner,
            "note": outcome_note,
        }
    )
    state.round_index += 1
    return state


class RefereeAgent(Agent):
    def __init__(self, state: GameState) -> None:
        super().__init__(name="rps_referee", description="Rock-Paper-Scissors-Plus referee agent.")
        self.state = state

    def interpret_intent(self, user_text: str) -> Optional[str]:
        normalized = user_text.strip().lower()
        for token in normalized.split():
            if token in VALID_MOVES:
                return token
        return None

    def choose_bot_move(self) -> str:
        moves = ["rock", "paper", "scissors"]
        if not self.state.bombs_used["bot"]:
            if self.state.round_index == 2 or self.state.bot_score < self.state.user_score:
                moves.append("bomb")
        return random.choice(moves)

    def play_round(self, user_text: str) -> str:
        round_number = self.state.round_index + 1
        user_move = self.interpret_intent(user_text)
        validation = validate_move_tool(user_move, "user", self.state)
        if validation["valid"] != "true":
            self.state = update_game_state_tool(
                self.state,
                user_move or "invalid",
                "none",
                "draw",
                f"Invalid input ({validation['reason']}). Round wasted.",
            )
            return self.format_round_response(round_number)

        bot_move = self.choose_bot_move()
        result = resolve_round_tool(user_move, bot_move)
        self.state = update_game_state_tool(
            self.state,
            user_move,
            bot_move,
            result["winner"],
            result["explanation"],
        )
        return self.format_round_response(round_number)

    def format_round_response(self, round_number: int) -> str:
        record = self.state.history[-1]
        winner = record["winner"]
        if winner == "user":
            winner_text = "You"
        elif winner == "bot":
            winner_text = "Bot"
        else:
            winner_text = "Draw"
        return "\n".join(
            [
                f"Round {round_number}/3",
                f"You: {record['user_move']} | Bot: {record['bot_move']}",
                f"Winner: {winner_text}",
                f"Reason: {record['note']}",
                f"Score: You {self.state.user_score} - Bot {self.state.bot_score}",
            ]
        )


def rules_text() -> str:
    return "\n".join(
        [
            "Best of 3 rounds. Valid moves: rock, paper, scissors, bomb (once per player).",
            "Bomb beats everything; bomb vs bomb is a draw.",
            "Invalid input wastes the round.",
            "Game ends automatically after 3 rounds.",
        ]
    )


def final_result(state: GameState) -> str:
    if state.user_score > state.bot_score:
        result = "User wins"
    elif state.bot_score > state.user_score:
        result = "Bot wins"
    else:
        result = "Draw"
    return "\n".join(
        [
            "Game Over",
            f"Final Score: You {state.user_score} - Bot {state.bot_score}",
            f"Result: {result}",
        ]
    )


def main() -> None:
    state = GameState()
    agent = RefereeAgent(state)
    print(rules_text())
    while agent.state.round_index < 3:
        user_text = input("Your move: ")
        print(agent.play_round(user_text))
    print(final_result(agent.state))


if __name__ == "__main__":
    main()
