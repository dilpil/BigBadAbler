# BigBadAbler - Autobattler Game

An autobattler game with minimal randomness where strategy and planning determine victory.

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Game

```
python main.py
```

## How to Play

### Shopping Phase
- **Left-click** on an empty tile (left side) to open the unit shop
- **Right-click** on your units to open the skill shop
- **Drag** units to reposition them
- **Drag** items from the item shop onto units to purchase
- Press **SPACE** to start combat

### Combat Phase
- Combat runs automatically
- Units will cast spells, attack, and move on their own
- Watch the battle unfold!

### Units
- **Necromancer** (N): Summons skeletons, dark magic specialist
- **Paladin** (P): Healing aura, tank and support
- **Pyromancer** (Y): AoE fireball, magical damage dealer
- **Berserker** (B): Attack speed buff, melee warrior

### Victory Conditions
- Win 20 rounds to achieve victory
- Lose all 5 lives and it's game over

## Controls
- **Left-click**: Select/purchase/drag
- **Right-click**: Open skill shop
- **Space**: Start combat / Pause combat
- **Period (.)**: Start combat paused / Advance one frame
- **Mouse hover**: View tooltips

## Testing

Run the test suite to verify game functionality:

```bash
python run_tests.py
```

Or run tests directly:
```bash
cd tests
python test_game.py
```

Tests cover:
- Board stability and unit management
- Game mechanics and purchasing
- Round reset functionality