# Rock-Paper-Scissors-Plus Referee (Google ADK)

A beginner-friendly AI Agent reference implementation using **Google ADK (Agent Development Kit)**.

This project demonstrates core AI agent concepts: **state management**, **tool design**, **user input handling**, and **orchestration logic** — all wrapped in a fun Rock-Paper-Scissors game!

> **Perfect for:** Learning how to build AI agents with structured logic, testing patterns, and clean separation of concerns.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation & Run
```bash
# Install dependencies
pip install google-adk

# Play the game
python main.py
```

### Run Tests
```bash
# Execute all test cases
python -m unittest test_main.py -v
```

---

## 🎮 Game Rules

| Aspect | Details |
|--------|---------|
| **Format** | Best-of-3 rounds (first to 2 wins) |
| **Valid Moves** | `rock` 🪨, `paper` 📄, `scissors` ✂️, `bomb` 💣 |
| **Win Logic** | rock beats scissors, paper beats rock, scissors beats paper |
| **Special** | Bomb beats everything; bomb vs bomb = draw |
| **Bomb Limit** | Each player can use bomb **once per game** |
| **Invalid Input** | Shows error, re-prompts without consuming a round |

---

## 💡 How It Works (Architecture)

### Three-Stage Turn Flow

When the user enters a move, the system processes it in three stages:

```
USER INPUT → INTERPRET INTENT → VALIDATE → RESOLVE → UPDATE STATE → DISPLAY RESULT
```

**Stage 1: Interpret Intent**
- Parse user text (e.g., "rock") into a recognized move
- Handle case-insensitivity and whitespace
- Return `None` if unrecognized → triggers validation error

**Stage 2: Validate & Execute**
- Check if move is legal (in VALID_MOVES)
- Check bomb hasn't been used twice
- Select bot's move (strategic or random)
- Determine round winner

**Stage 3: Update & Display**
- Mutate game state (scores, history, bombs used)
- Format friendly output with emojis and reasons
- Increment round counter

### Core Components

#### 1. **GameState** (dataclass)
Holds all persistent game information:

```python
GameState(
    round_index=0,           # How many rounds completed (0-3)
    user_score=0,            # User wins so far
    bot_score=0,             # Bot wins so far
    bombs_used={'user': False, 'bot': False},  # Track bomb usage
    history=[...]            # List of past rounds for replay/audit
)
```

**Why:** Separates data from logic. Easy to test, serialize, or replay.

#### 2. **RefereeAgent** (Orchestrator)
The "brain" that coordinates game flow. **Not** an LLM agent—just a plain class managing the rules.

**Key Methods:**
- `interpret_intent(user_text)` → Extract move from user input
- `choose_bot_move()` → Pick bot's next move (slightly smart: uses bomb when trailing)
- `play_round(user_text)` → **Main entry point**: orchestrates one full turn
- `format_round_response(round_number)` → Pretty-print round results

#### 3. **Tool Functions** (Pure Logic)
Three helper functions that handle specific tasks. Think of tools as **testable, reusable logic blocks**:

- **`validate_move_tool(move, player, state)`**
  - Checks: move exists? Bomb already used?
  - Returns: `{valid: bool, reason: str}` (structured, not text)
  - **Why:** Separates validation rules from UI

- **`resolve_round_tool(user_move, bot_move)`**
  - Takes two moves, returns winner + explanation
  - Handles all win cases: bomb, same move, RPS logic
  - **Why:** Pure function, no state mutation—easy to test

- **`update_game_state_tool(state, moves, winner, note)`**
  - Mutates state: increment scores, record history, mark bombs used
  - **Why:** Centralizes state mutations; makes debugging easier

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────┐
│      Game Loop (main)           │
│  for round in 3 rounds:         │
│    → play_round(user_input)     │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   RefereeAgent.play_round()     │ ← Orchestrator
│  1. interpret_intent()          │
│  2. validate_move_tool()        │
│  3. choose_bot_move()           │
│  4. resolve_round_tool()        │
│  5. update_game_state_tool()    │
│  6. format_round_response()     │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   GameState (persistent)        │
│  • Scores, history, bombs       │
└─────────────────────────────────┘
```

---

## 📊 State Persistence Example

```python
# Start of game
state = GameState()  # round_index=0, scores=0-0, bombs unused

# After round 1: user plays rock, bot plays scissors
play_round("rock")
# state becomes: round_index=1, user_score=1, bomb_used=unchanged

# After round 2: user plays paper, bot plays rock
play_round("paper")
# state becomes: round_index=2, user_score=2

# After round 3: user plays bomb, bot plays scissors
play_round("bomb")
# state becomes: round_index=3, user_score=3, bombs_used={'user': True, 'bot': False}

# Game ends - check final score
```

---

## 🧪 Testing Strategy

The project includes **6 unit tests** covering:

1. **Tool Validation** (`validate_move_tool`)
   - Reject invalid moves
   - Reject reused bombs

2. **Round Resolution** (`resolve_round_tool`)
   - Handle draws (same move, bomb vs bomb)
   - Determine correct winner for all move combinations

3. **State Updates** (`update_game_state_tool`)
   - Score increments
   - History recording
   - Bomb tracking

4. **Agent Orchestration** (`RefereeAgent`)
   - Invalid input doesn't consume a round
   - Intent parsing requires exact matches

**Run tests:**
```bash
python -m unittest test_main.py -v
```

---

## 🎯 Learning Path for Beginners

### Concept 1: State Management
- Open `main.py`, find `GameState` dataclass
- Notice how it's passed to tool functions, not LLM prompts
- **Why:** Structured data is reliable and testable

### Concept 2: Tool Design
- Look at the three tool functions
- Notice they're **pure functions** (no side effects except return)
- **Why:** Easy to unit test and reason about

### Concept 3: Agent Orchestration
- Read `RefereeAgent.play_round()`
- Follow the flow: interpret → validate → resolve → update → display
- **Why:** Clear, sequential logic beats LLM decision-making for games

### Concept 4: Input Handling
- `interpret_intent()` does exact-match parsing
- Invalid input triggers re-prompt without advancing round
- **Why:** User-facing agents need clear error messages

---

## 💬 Example Interaction

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

Your move: invalid
Invalid move.
Reason: unknown move.
Please enter rock, paper, scissors, or bomb.

Your move: paper

==== Round Result ====
Round 2/3
Moves: You=paper 📄 | Bot=rock 🪨
Winner: You
Reason: paper beats rock.
Score: You 2 - Bot 0
======================

Game Over
Final Score: You 2 - Bot 0
Result: User wins
```

---

## 📚 Key Takeaways

| Concept | In This Project |
|---------|-----------------|
| **State** | `GameState` persists across turns; passed to tools |
| **Validation** | Separate tool function; returns structured results |
| **Orchestration** | `play_round()` coordinates the workflow |
| **Testing** | Pure functions are easy to unit test |
| **User Experience** | Clear errors + re-prompts without consuming turns |
| **Extensibility** | Add new moves or rules by updating constants + tools |

---

## 🚀 Extension Ideas

- **Add multiplayer:** Track players in a dict instead of hardcoded "user"/"bot"
- **Implement AI strategy:** Replace random bot moves with ML-based predictions
- **Store game replay:** Serialize `state.history` to JSON for analysis
- **Statistics:** Calculate win rates, move frequencies
- **Web UI:** Wrap the agent in a FastAPI app

---

## 📖 Files Overview

| File | Purpose |
|------|---------|
| `main.py` | Game logic, agent, tools, CLI loop |
| `test_main.py` | Unit tests for tools and agent behavior |
| `README.md` | This guide |

---

## 🤔 FAQ for Beginners

**Q: Why not use an LLM agent here?**
A: This game has deterministic rules. An LLM would be overkill and introduce unpredictability. Use structured logic for games, tools for external APIs.

**Q: What is a "tool" in agents?**
A: A tool is a Python function that an agent can call. Here, tools validate moves, resolve outcomes, and update state. In real agents, tools might call APIs, databases, or calculators.

**Q: Why is GameState separate from the agent?**
A: It makes testing easier and keeps concerns separate. You can test state updates without running the full agent.

**Q: How would I add a third player?**
A: Generalize `bombs_used` to a dict of players, update `play_round()` to accept a player name, loop over players.
