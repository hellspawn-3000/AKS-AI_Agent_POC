# Rock-Paper-Scissors-Plus Referee (ADK)

This project is a minimal CLI chatbot that acts as a referee for a best-of-3 Rock-Paper-Scissors-Plus game. It enforces rules, tracks state across turns, and ends automatically after 3 rounds. The implementation is intentionally small and readable for beginner AI enthusiasts.

## Quick start
```bash
pip install google-adk
python main.py
```

## Game rules (short version)
- Best of 3 rounds.
- Valid moves: rock, paper, scissors, bomb (once per player).
- Move emojis: rock 🪨, paper 📄, scissors ✂️, bomb 💣
- Bomb beats everything; bomb vs bomb is a draw.
- Invalid input triggers a warning and re-prompt (round does not advance).

## How the chatbot works (high level)
Each user turn goes through the same three stages:
1) Intent understanding: extract a move from the user's exact input.
2) Game logic: validate the move, select the bot move, resolve winner.
3) Response generation: show round summary and current score.

That flow happens inside `RefereeAgent.play_round`, which calls ADK tools for validation, resolution, and state updates.

## State model (what we store)
The game state lives in `GameState` and persists across turns:
- `round_index`: how many rounds have been completed
- `user_score` and `bot_score`
- `bombs_used`: whether each player has used bomb
- `history`: a list of round records for reporting

State is stored in memory and passed into tools for validation or mutation (so it is not just text in the prompt).

## Agent and tool design (what does what)
### Agent (orchestrator)
`RefereeAgent` is the control center:
- `interpret_intent`: parses exact inputs like `rock`, `paper`, `scissors`, `bomb`
- `choose_bot_move`: picks a move for the bot
- `play_round`: coordinates the full turn
- `format_round_response`: prints the round results

### Tools (explicit ADK functions)
Tools keep game logic separate and testable:
- `validate_move_tool`: checks if a move is valid and bomb usage is allowed
- `resolve_round_tool`: decides who wins the round
- `update_game_state_tool`: mutates scores, history, and bomb usage

## Input parsing (exact)
The parser expects an exact move: `rock`, `paper`, `scissors`, or `bomb`.
If the input is anything else, the bot warns the user and asks again without consuming a round.

## Example interaction
```
Best of 3 rounds. Valid moves: rock, paper, scissors, bomb (once per player).
Move emojis: rock 🪨, paper 📄, scissors ✂️, bomb 💣
Bomb beats everything; bomb vs bomb is a draw.
Invalid input triggers a warning and re-prompt.
Game ends automatically after 3 rounds.
Your move: rock
==== Round Result ====
Round 1/3
Moves: You=rock 🪨 | Bot=scissors ✂️
Winner: You
Reason: rock beats scissors.
Score: You 1 - Bot 0
======================
```

## Tests
```bash
python -m unittest
```

## Tradeoffs
- Bot strategy is intentionally simple (random with occasional bomb) to keep logic easy to follow.

## With more time
- Add property-based tests for move parsing and scoring.
- Tune bot strategy for more interesting play.
- Support configurable match lengths (best-of-5, best-of-7).
