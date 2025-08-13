This is an autobattler.

However, instead of being based on high randomness and variance, the player is given the opportunity to build a team from whatever units and abilities they want, with the only source of randomness being the item shop.

### Progression

Each round the player gets 100 gold to spend on characters, items, and abilities.
The player can always purchase any character or ability each round.
Items however, must be purchased from a rotating shop- the shop has a different set of 10 items available for purchase each round.
Each character has a unique starting ability and a pool of 10-20 abilities that can be purchased for it.  Some buyable abilities are available to multiple units.
Characters have a maximum of 5 abilities and 3 items.
Items can be moved between characters each round, abilities cannot.

The player starts with 5 lives.  Losing a round subtracts 1 life.
Losing all lives results in a defeat.
Winning a total of 20 rounds results in victory.

After each round, all player units and spells are reset (original positions, max hp, cleared of status effects, cooldowns reset, ect.)


### Combat

Each round, the players team fights an enemy team.
During the shopping phase, the player can see information about the enemy team- unit positioning, items and abilities equipped, ect.
The player can position their units in whatever way he sees fit each round.
Combat is done in real time, and once it begins, the player has no input into how it plays out.
For more details, see Combat.MD

### Game modes

The most common game mode is single player async.  In this mode, you have unlimited time to think about each decision you make, and you see the enemy team before you spend your gold and position your units.  Generally in this mode, you play against a very large pool of players- perhaps all the players who are playing the current patch.

The game can also be played in real time or tournament mode, where you have limited time- 1 minute, or 24 hours- to make decisions, and you see the enemy team's previous turn rather than exactly what you will fight.  In these modes, you generally play against a smaller pool of players.

Players can make also make custom game modes.  These can have custom patches (changes to units and item numbers), and can have characteristics of async or tournament modes (timers, pool sizes, fights per round, ect).



### Board
The game board is 8x8
The player units start on the left hand side, the enemy units start on the right hand side.
Each tile can be occupied by only one unit at a time (When a unit begins movement into a tile, it vacates its previous tile immediately, and occupies the new one immediately, though visually it appears to smoothly walk from one tile to the other)
Distances on the board are always measured in chebyshev distance.

### Unit stats

All units have the following stats:

Hitpoints (HP): The maximum amount of damage a unit can take before dying
HP Regen (HP/s): hitpoints regained per second
Mana (MP): The maximum amount of mana a unit can spend on spells
MP Regen (MP/s): mana regained per second
Strength (str): percentage bonus to attack damage, also used by some abilities
Int (int): percentage bonus to ability strength
Armor (ar): incoming physical damage is multiplied by 100 / (100 + armor), so each point of armor increases its effective hp against physical damage by 1%
Resist (mr): incoming magical damage is multiplied by 100 / (100 + armor), so each point of armor increases its effective hp against magical damage by 1%

Attack damage (AD): base attack damage
Attack range: max attack range
Attack speed (AS): each point increases the number of attacks per second by 1%, so 100 attack speed doubles a units attack speed.  0 attack speed = 1 attack per second.


### Unit behavior

A units behavior state is either idle, walking, attacking, or casting.
A unit always prefers casting to attacking, attacking to walking, and walking to idling.
A unit always walks towards the nearest enemy unit if it cannot attack or cast, using A star pathfinding to go around blocked tiles if needed.
Units will always prefer to attack whatever unit they attacked previously, if possible.  This unit is referred to as their 'target'.


### Skills

Skills have the following stats:

Passive: boolean value for if the skill is passive or not, defaults to true.
Cast Time: time in seconds required to cast the skill (if it is castable- default to None for passive skills)
Cooldown Time: time in seconds the skill cannot be cast after it is cast.  The skill is 'on cooldown' during this time.  Generally None for passive skills, but can be used for internal cooldown mechanisms for passive skills.
Mana Cost: Amount of mana required to cast the skill.  None for passive skills.

When a unit starts to cast a spell, the mana cost is immediately deducted.

By default, a spell will execute effects once the unit has spend the entire cast time casting(channeling) the spell.  However, there are some spells that perform effects while the spell is being channeled.

All skills, active or passive, can have triggers that activate in response to events (damage, death, summon, attack, ect).

### Files

board.py - maintains the positions of units, lists of units per team.  Supports queries for querying distance, finding units in an area, ect.  Also contains methods for raising events and triggering skills/items.
unit.py - maintains the state of one unit.  Contains methods for dealing damage, casting spells, ect.
skill.py - maintains the state of one skill.
game.py - maintains the state of one game run.  Knows the players owned units, items, gold, health, current level, current game mode, ect.
PyUI.py - pygame UI for the game.  Contains all visual rendering logic.

content/units.py - factory methods for each available character (unit type)
content/skills.py - class for each skill, list of factory methods for each available skill
content/items.py - class for each item, list of factory methods for each available item

### Time and Framerate

The game is designed to run at a fixed 60 frames per second.  Slowdown may happen, but will be ignored.  So each frame will be assumed to be 1/60th of a second for mechanical purposes.

### Projectiles

Ranged attacks and many skills use projectiles to execute their effect- they do not immediately modify the game world, but create a projectile that makes some effect on hitting its target.
Projectiles can be dodged, reflected, redirected, ect,
Projectiles generally execute their effect through the OnLand(target) callback, and should execute their effect on the given target (which may even be the source of the projectile!)

### Status Effects

Some items or skills can apply statuses to units.  Status effects can deal damage over time, do something else each frame, temporarily modify a unit's stats, or respond to triggers.  Status effects are generally temporary, removed after some duration.

Examples of status effects:
poison: deal a small amount of damage every 5 frames
weakness: reduce all outgoing damage by 25%
dumbfound: stop all spells from recharging for the duration
regeneration: regenerate a small amount of health every 5 frames
protection: double a unit's armor and mr.

### Events

Various things trigger events: damage taken, damage dealt, death, summoning, attacking, casting.
Items and skills can have event triggers that respond to the events.
Whenever an event happens, board.raise_event will iterate over all units, and then over each skill and item and status on that unit, to trigger any triggers that exist for that event.

### Visuals

During either phase, the main visual is simply the board.  On the left is the players team, which can be dragged around and rearranged, on the right is the enemy team.
Visual logic should be entirely contained in PyUI.py.

# Color Palette
The color palette of the game is based on a synthwave/vaporwave aesthetic, with purple, pink, reds, and blues being the most common colors.

# Shopping Visuals
During the shopping phase, the player can click on an empty board slot to open the character shop.  This displays all available units in a grid.  Clicking one will purchase it, closing the character shop, and placing that character at the slot which was clicked.
Clicking a unit will open the ability shop for that unit, which looks similar to the character shop, but is populated with all available abilities for that unit.  Clicking an ability buys it and closes the ability shop.
During the shopping phase, the area beneath the board is devoted to the item shop.  The items and their prices are lined up horizontally.  Items can be purchased by dragging them onto characters.
Items, characters, and abilities that cannot be purchased, either due to lack of funds or lack of slots, are greyed out and cannot be dragged.

# Combat Visuals

During the combat phase, the board stays in the same position, but the shopping panel is replaced by a message log.

# Board Visuals

The board is the main visual feature of the game, persisting through

Units represented by colored squares
Projectiles are represented by small circles
Units have health and mana bars at the bottom of their square
Buffs and debuffs are represented by small squares that stack right to left at the top of the unit square
Units have a border that shows which team they are on
Units have a giant Letter in the middle of their square.  This letter, its color, and the color of their square, indicate the unit's type.

On taking damage, a unit flashes white and emites a small burst of particles.  A floating damage number appears briefly to indicate the amount (and via color, type- white for physical blue for magical) of damage.

On dying, the unit flashes red 4 times before vanishing.

On casting, the unit flashes purple and jumps up a bit.
On attacking, the unit bumps towards its target a bit.

# Tooltip Visuals
During either phase, mousing over a unit, item, or skill will show a tooltip explaining what that thing does.
