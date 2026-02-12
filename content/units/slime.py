import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import DamageOverTimeEffect

class Slime(Unit):
    def __init__(self):
        super().__init__("Slime", UnitType.SLIME)
        self.max_hp = 300
        self.hp = self.max_hp
        self.attack_damage = 20
        self.attack_range = 2  # Ranged
        self.attack_speed = 0
        self.strength = 0
        self.intelligence = 15
        self.armor = 10
        self.magic_resist = 10

        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(Mitosis())

    def attack(self, target):
        """Override attack to apply poison on hit"""
        super().attack(target)
        # Apply poison on every attack
        if target and target.is_alive():
            poison = DamageOverTimeEffect("Slime Poison", 3.0, 10.0, "magical")
            poison.source = self
            target.add_status_effect(poison)

    @staticmethod
    def get_cost() -> int:
        return 30  # Cheap unit

def create_slime() -> Slime:
    return Slime()


# ===== SLIME SKILLS =====

class Mitosis(Skill):
    """Make an itemless copy of self"""
    def __init__(self):
        super().__init__("Mitosis", "Create an itemless copy of self")
        self.cast_time = 0.3
        self.mana_cost = 40

    def should_cast(self, caster) -> bool:
        if not caster.board:
            return False
        # Check if there's space nearby
        position = self._find_nearby_position(caster)
        return position is not None

    def execute(self, caster):
        if not caster.board:
            return

        position = self._find_nearby_position(caster)
        if not position:
            return

        # Create copy without items
        copy = Slime()
        copy.max_hp = int(caster.max_hp * 0.75)  # 75% HP
        copy.hp = copy.max_hp
        copy.attack_damage = int(caster.attack_damage * 0.75)  # 75% damage
        copy.is_summoned = True
        copy.summoner = caster

        # Don't copy items - that's the point of this skill

        # Place on board
        caster.board.add_unit(copy, position[0], position[1], caster.team)

        if caster.board:
            from visual_effect import VisualEffectType
            caster.board.add_visual_effect(VisualEffectType.ARCANE, position[0], position[1])

    def _find_nearby_position(self, unit):
        """Find an empty position near the unit"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                x, y = unit.x + dx, unit.y + dy
                if 0 <= x < 8 and 0 <= y < 8:
                    if not unit.board.get_unit_at(x, y):
                        # Check if position is on correct side
                        if unit.team == "player" and x < 4:
                            return (x, y)
                        elif unit.team == "enemy" and x >= 4:
                            return (x, y)
        return None
