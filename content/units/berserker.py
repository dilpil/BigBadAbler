import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import StatusEffect, StatModifierEffect
import math

class Berserker(Unit):
    def __init__(self):
        super().__init__("Berserker", UnitType.BERSERKER)
        self.max_hp = 1000
        self.hp = self.max_hp
        self.max_mp = 70
        self.mp = 0
        self.attack_damage = 70
        self.attack_range = 1
        self.strength = 25
        self.attack_speed = 0  # 1.0 attacks per second
        self.armor = 35
        self.magic_resist = 35
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        self.set_spell(Frenzy())
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_berserker() -> Berserker:
    """Factory function to create a berserker"""
    return Berserker()


# ===== CUSTOM STATUS EFFECTS =====

class FrenzyEffect(StatusEffect):
    """Custom status effect for Frenzy that provides attack speed, lifesteal, and optionally armor. Stacks."""
    def __init__(self, duration: float = None):  # None means until end of combat
        from status_effect import StackType
        super().__init__("Frenzy", duration, StackType.STACK_INTENSITY)
        self.attack_speed_bonus = 10
        self.lifesteal_percent = 10
        self.armor_bonus = 0
        self.magic_resist_bonus = 0

    def apply(self, unit):
        super().apply(unit)
        # Apply stat bonuses
        unit.attack_speed += self.attack_speed_bonus
        unit.armor += self.armor_bonus
        unit.magic_resist += self.magic_resist_bonus

    def remove(self, unit):
        # Remove stat bonuses (multiply by stacks)
        unit.attack_speed -= self.attack_speed_bonus * self.stacks
        unit.armor -= self.armor_bonus * self.stacks
        unit.magic_resist -= self.magic_resist_bonus * self.stacks
        super().remove(unit)
        
    def on_event(self, event_type: str, **kwargs):
        # Handle lifesteal on attack (scales with stacks)
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            damage_dealt = kwargs.get("damage", 0)
            if damage_dealt > 0:
                heal_amount = damage_dealt * (self.lifesteal_percent * self.stacks / 100.0)
                self.unit.heal(heal_amount, self.unit)


# ===== BERSERKER SKILLS =====

class Frenzy(Skill):
    def __init__(self):
        super().__init__("Frenzy", "Gain 10% attack speed and 5% lifesteal until end of combat")
        self.cast_time = 0.3
        self.mana_cost = 40
        self.range = 0
        
    def should_cast(self, caster) -> bool:
        # Always cast when we have mana - Frenzy stacks!
        return True
        
    def execute(self, caster):
        effect = FrenzyEffect()
        effect.source = caster
        caster.add_status_effect(effect)
