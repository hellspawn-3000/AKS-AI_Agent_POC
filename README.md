# Rock-Paper-Scissors-Plus Referee (ADK)

This is a minimal CLI chatbot that acts as a referee for a best-of-3 Rock-Paper-Scissors-Plus game. It enforces rules, tracks state across turns, and ends automatically after 3 rounds.

## State model
- `GameState` holds `round_index`, `user_score`, `bot_score`, `bombs_used`, and `history`.
- State is stored in memory and passed into tools for validation and mutation (not kept only in prompts).

## Agent and tool design
- `RefereeAgent` separates responsibilities:
  - Intent understanding: `interpret_intent` extracts the user's move from text.
  - Game logic: `choose_bot_move`, plus tool calls for validation and resolution.
  - Response generation: `format_round_response`.
- Tools (ADK) are explicit:
  - `validate_move_tool` checks validity and bomb usage.
  - `resolve_round_tool` determines the round outcome.
  - `update_game_state_tool` mutates scores, history, and round count.

## Tradeoffs
- The bot move uses a simple heuristic (random with optional bomb usage) rather than a sophisticated strategy to keep logic minimal and clear.
- A small fallback decorator is included in `main.py` so the script can run without ADK installed; the ADK tools and agent structure remain visible for review.

## With more time
- Add property-based tests for move parsing and scoring.
- Tune bot strategy for more interesting play.
- Support configurable match lengths (best-of-5, best-of-7).

## Tests
```bash
python -m unittest
```

## Run
```bash
python main.py
```
