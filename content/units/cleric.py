import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import StatModifierEffect

class Cleric(Unit):
    def __init__(self):
        super().__init__("Cleric", UnitType.CLERIC)
        self.max_hp = 550
        self.hp = self.max_hp
        self.max_mp = 70
        self.mp = 0
        self.attack_damage = 40
        self.attack_range = 3  # Ranged unit
        self.attack_speed = -20  # 0.8 attacks per second
        self.strength = 5
        self.armor = 20
        self.magic_resist = 30

        # Set default skill immediately upon creation
        self._set_default_skill()

    def _set_default_skill(self):
        """Set the default skill for this unit"""
        self.set_spell(Heal())

    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 45

def create_cleric() -> Cleric:
    """Factory function to create a cleric"""
    return Cleric()


# ===== CLERIC SKILLS =====

class Heal(Skill):
    def __init__(self):
        super().__init__("Heal", "Heal the lowest HP ally for 400")
        self.cast_time = 1.5
        self.mana_cost = 60
        self.heal_amount = 400

    def should_cast(self, caster) -> bool:
        # Cast if there are injured allies
        if not caster.board:
            return False
        allies = caster.board.get_allied_units(caster.team)
        for ally in allies:
            if ally.is_alive() and ally.hp < ally.max_hp:
                return True
        return False

    def execute(self, caster):
        if not caster.board:
            return

        # Find lowest HP ally (by percentage)
        allies = caster.board.get_allied_units(caster.team)
        injured_allies = [ally for ally in allies if ally.is_alive() and ally.hp < ally.max_hp]

        if not injured_allies:
            return

        # Find ally with lowest HP percentage
        target = min(injured_allies, key=lambda a: a.hp / a.max_hp)

        # Heal the target
        target.heal(self.heal_amount, caster)

        # Visual effect
        if caster.board:
            from visual_effect import VisualEffectType
            caster.board.add_visual_effect(VisualEffectType.HOLY, target.x, target.y)
