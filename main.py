"""Rock-Paper-Scissors-Plus Referee Agent

A beginner-friendly AI agent that demonstrates:
- State management (GameState persists across turns)
- Tool design (pure functions for validation, resolution, state updates)
- Agent orchestration (RefereeAgent coordinates the game flow)
- Input handling and error management

Usage:
    python main.py  # Play a 3-round game against the bot
"""

import random
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from google.adk import Agent
from google.adk.tools import FunctionTool


# ============================================================================
# GAME CONSTANTS
# ============================================================================

# Set of all valid player moves. 'bomb' is a special move that beats everything.
VALID_MOVES = {"rock", "paper", "scissors", "bomb"}

# Defines what each move beats in classic Rock-Paper-Scissors (not bomb).
# Key: player's move, Value: what it beats
RPS_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

# Emoji labels for friendly CLI display.
MOVE_EMOJI = {
    "rock": "rock 🪨",
    "paper": "paper 📄",
    "scissors": "scissors ✂️",
    "bomb": "bomb 💣",
    "none": "none",
}
@dataclass
class ValidationResult:
    """Structured response from validate_move_tool().
    
    Why structured output matters:
    - Agent code can easily check result['valid'] instead of parsing strings
    - Tool outputs are consistent and testable
    - Easier to extend (e.g., add error codes) later
    
    Attributes:
        valid: Boolean indicating if the move is legal
        reason: Human-readable explanation for invalid moves
    """

    valid: bool
    reason: str


@dataclass
class ResolutionResult:
    """Structured response from resolve_round_tool().
    
    Attributes:
        winner: 'user', 'bot', or 'draw'
        explanation: Reason why (e.g., 'rock beats scissors.')
    """

    winner: str
    explanation: str


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class GameState:
    """Complete game state that persists across all 3 rounds.
    
    Attributes:
        round_index: Number of rounds completed (0-2, incremented after each round)
        user_score: Number of rounds won by the user
        bot_score: Number of rounds won by the bot
        bombs_used: Dict tracking if each player has used their one bomb
        history: List of dicts recording all past rounds for replay/analysis
    
    Design Note:
        This dataclass is deliberately separate from RefereeAgent to:
        1. Make it easy to test state updates independently
        2. Allow serialization (to JSON, database, etc.)
        3. Keep data and logic concerns separated (good practice)
    """

    round_index: int = 0
    user_score: int = 0
    bot_score: int = 0
    bombs_used: Dict[str, bool] = field(default_factory=lambda: {"user": False, "bot": False})
    history: List[Dict[str, str]] = field(default_factory=list)


# ============================================================================
# TOOL FUNCTIONS
# ============================================================================
# Tools are pure functions that handle specific game logic.
# They take data (no side effects) and return results.
# Design benefit: Easy to test, reuse, and reason about.


def validate_move_tool(move: Optional[str], player: str, state: GameState) -> Dict[str, object]:
    """Validate a player's move against game rules.
    
    This tool checks two things:
    1. Is the move in VALID_MOVES? (prevents typos)
    2. Has the player already used their bomb? (enforces one-per-game limit)
    
    Args:
        move: The move string ('rock', 'paper', 'scissors', 'bomb', or None/invalid)
        player: 'user' or 'bot' (for bomb tracking)
        state: Current game state (to check bomb usage)
    
    Returns:
        Dict with keys:
        - 'valid': bool (True if move is allowed)
        - 'reason': str (explanation for invalid moves)
    
    Examples:
        >>> validate_move_tool('rock', 'user', GameState())
        {'valid': True, 'reason': 'ok'}
        
        >>> validate_move_tool('bomb', 'user', GameState(bombs_used={'user': True}))
        {'valid': False, 'reason': 'bomb already used'}
    """
    if not move:
        return asdict(ValidationResult(valid=False, reason="empty input"))
    if move not in VALID_MOVES:
        return asdict(ValidationResult(valid=False, reason="unknown move"))
    if move == "bomb" and state.bombs_used.get(player, False):
        return asdict(ValidationResult(valid=False, reason="bomb already used"))
    return asdict(ValidationResult(valid=True, reason="ok"))


def resolve_round_tool(user_move: str, bot_move: str) -> Dict[str, str]:
    """Determine the winner of a single round given two moves.
    
    Win logic (in order of precedence):
    1. Same move → draw
    2. Bomb vs bomb → draw
    3. Bomb vs anything else → bomb wins
    4. Standard Rock-Paper-Scissors logic (RPS_BEATS)
    
    Args:
        user_move: Validated move from player
        bot_move: Validated move from bot
    
    Returns:
        Dict with keys:
        - 'winner': 'user', 'bot', or 'draw'
        - 'explanation': Human-readable reason (used in UI output)
    
    Note:
        This is a pure function (no state mutation), making it easy to test.
    """
    if user_move == bot_move:
        return asdict(ResolutionResult(winner="draw", explanation="Same move."))
    if user_move == "bomb" and bot_move == "bomb":
        return asdict(ResolutionResult(winner="draw", explanation="Bomb vs bomb is a draw."))
    if user_move == "bomb":
        return asdict(ResolutionResult(winner="user", explanation="Bomb beats all other moves."))
    if bot_move == "bomb":
        return asdict(ResolutionResult(winner="bot", explanation="Bomb beats all other moves."))
    if RPS_BEATS[user_move] == bot_move:
        return asdict(ResolutionResult(winner="user", explanation=f"{user_move} beats {bot_move}."))
    return asdict(ResolutionResult(winner="bot", explanation=f"{bot_move} beats {user_move}."))


def update_game_state_tool(
    state: GameState,
    user_move: str,
    bot_move: str,
    winner: str,
    outcome_note: str,
) -> GameState:
    """Update game state with the result of a completed round.
    
    This tool performs three updates:
    1. Mark bombs as used (if either player played bomb)
    2. Increment the winner's score
    3. Record the round in history for later analysis/replay
    4. Increment round_index
    
    Args:
        state: Current GameState (modified and returned)
        user_move: The user's move
        bot_move: The bot's move
        winner: 'user', 'bot', or 'draw'
        outcome_note: Why the winner won (from resolve_round_tool)
    
    Returns:
        Updated GameState with incremented scores and history
    
    Design Note:
        This is the only function that mutates state.
        Centralizing mutations here makes debugging easier.
    """
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


# ============================================================================
# AGENT (ORCHESTRATOR)
# ============================================================================


class RefereeAgent:
    """Game referee that orchestrates a 3-round Rock-Paper-Scissors match.
    
    This is NOT an LLM agent—it's a deterministic orchestrator that:
    - Parses user input into moves
    - Coordinates validation, resolution, and state updates
    - Formats friendly game output
    
    Key principle: Separation of concerns
    - Agent: orchestration (what to do and when)
    - Tools: game logic (validation, resolution, state updates)
    - GameState: data persistence
    """
    
    def __init__(self, state: GameState) -> None:
        """Initialize the referee with a game state.
        
        Args:
            state: GameState object to manage throughout the match
        """
        self.state = state

    def interpret_intent(self, user_text: str) -> Optional[str]:
        """Parse user text into a recognized move.
        
        This implements exact-match parsing:
        - Lowercase input
        - Strip whitespace
        - Check against VALID_MOVES
        
        Why exact-match? Because deterministic games should have clear rules.
        No fuzzy matching (e.g., 'r' → 'rock') to avoid confusion.
        
        Args:
            user_text: Raw user input (e.g., 'Rock', '  paper  ')
        
        Returns:
            Recognized move string, or None if unrecognized
        
        Examples:
            >>> agent.interpret_intent('rock')
            'rock'
            >>> agent.interpret_intent('BOMB')
            'bomb'
            >>> agent.interpret_intent('lizard')
            None  # Triggers validation error in play_round()
        """
        normalized = user_text.strip().lower()
        return normalized if normalized in VALID_MOVES else None

    def choose_bot_move(self) -> str:
        """Select the bot's next move.
        
        Strategy (intentionally simple to keep code readable):
        - Randomly pick from [rock, paper, scissors]
        - If bot hasn't used bomb AND (it's round 3 OR bot is losing), add bomb to choices
        - Randomly pick from final pool
        
        Why simple? Beginners can understand it. Replace this with ML/strategy later.
        
        Returns:
            One of VALID_MOVES: 'rock', 'paper', 'scissors', or 'bomb'
        """
        moves = ["rock", "paper", "scissors"]
        if not self.state.bombs_used["bot"]:
            if self.state.round_index == 2 or self.state.bot_score < self.state.user_score:
                moves.append("bomb")
        return random.choice(moves)

    def play_round(self, user_text: str) -> str:
        """Execute one complete game round.
        
        Flow (the three-stage model explained in README):
        1. INTERPRET: Parse user text → move
        2. VALIDATE: Check move is legal via validate_move_tool()
           - If invalid: return error message, DON'T advance round
        3. EXECUTE & RESOLVE:
           - Bot picks move via choose_bot_move()
           - Determine winner via resolve_round_tool()
        4. UPDATE: Apply outcome to state via update_game_state_tool()
        5. DISPLAY: Format friendly output via format_round_response()
        
        Args:
            user_text: Raw user input (e.g., 'rock')
        
        Returns:
            String to display to user:
            - On invalid input: error message (round not consumed)
            - On valid input: round summary with scores
        """
        round_number = self.state.round_index + 1
        user_move = self.interpret_intent(user_text)
        validation = validate_move_tool(user_move, "user", self.state)
        if not validation["valid"]:
            return "\n".join(
                [
                    "Invalid move.",
                    f"Reason: {validation['reason']}.",
                    "Please enter rock, paper, scissors, or bomb.",
                ]
            )

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
        """Format the last round into a user-friendly summary.
        
        Retrieves the last round from state.history and formats it as:
        ```
        ==== Round Result ====
        Round X/3
        Moves: You=... | Bot=...
        Winner: ...
        Reason: ...
        Score: You X - Bot Y
        ======================
        ```
        
        Args:
            round_number: 1, 2, or 3 (for display)
        
        Returns:
            Formatted string ready to print
        """
        record = self.state.history[-1]
        winner = record["winner"]
        if winner == "user":
            winner_text = "You"
        elif winner == "bot":
            winner_text = "Bot"
        else:
            winner_text = "Draw"
        user_move = MOVE_EMOJI.get(record["user_move"], record["user_move"])
        bot_move = MOVE_EMOJI.get(record["bot_move"], record["bot_move"])
        return "\n".join(
            [
                "",
                "==== Round Result ====",
                f"Round {round_number}/3",
                f"Moves: You={user_move} | Bot={bot_move}",
                f"Winner: {winner_text}",
                f"Reason: {record['note']}",
                f"Score: You {self.state.user_score} - Bot {self.state.bot_score}",
                "======================",
                "",
            ]
        )


# ============================================================================
# HELPER FUNCTIONS (Display)
# ============================================================================


def rules_text() -> str:
    """Return the game rules for display at match start.
    
    Shown once at the beginning so players understand the rules.
    """
    return "\n".join(
        [
            "",
            "Best of 3 rounds. Valid moves: rock, paper, scissors, bomb (once per player).",
            "Move emojis: rock 🪨, paper 📄, scissors ✂️, bomb 💣",
            "Bomb beats everything; bomb vs bomb is a draw.",
            "Invalid input triggers a warning and re-prompt.",
            "Game ends automatically after 3 rounds.",
            "",
        ]
    )


def final_result(state: GameState) -> str:
    """Format the final score and outcome.
    
    Shown after all 3 rounds are complete.
    """
    if state.user_score > state.bot_score:
        result = "User wins"
    elif state.bot_score > state.user_score:
        result = "Bot wins"
    else:
        result = "Draw"
    return "\n".join(
        [
            "",
            "Game Over",
            f"Final Score: You {state.user_score} - Bot {state.bot_score}",
            f"Result: {result}",
            "",
        ]
    )


def main() -> None:
    """Main entry point: Initialize game and play 3 rounds.
    
    Flow:
    1. Create GameState (empty)
    2. Create RefereeAgent (with state)
    3. Display rules
    4. Loop: Read user input → play_round() → display output
    5. Display final result
    
    This is the user-facing CLI loop. To integrate into a larger system
    (e.g., web server, Discord bot), extract play_round() logic.
    """
    state = GameState()
    agent = RefereeAgent(state)
    print(rules_text())
    while agent.state.round_index < 3:
        user_text = input("Your move: ")
        print(agent.play_round(user_text))
    print(final_result(agent.state))


# Entry point guard: ensures main() only runs when script is executed directly
# (not when imported as a module elsewhere)
if __name__ == "__main__":
    main()
