import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import StatModifierEffect

class Berserker(Unit):
    def __init__(self):
        super().__init__("Berserker", UnitType.BERSERKER)
        self.max_hp = 750
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
        default_skill = create_berserker_skill("bloodlust")
        if default_skill:
            self.set_spell(default_skill)
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return []  # No passive skills yet
    
    def get_passive_skill_cost(self, skill_name: str) -> int:
        """Get the cost of a passive skill"""
        return 30  # Default cost
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_berserker() -> Berserker:
    """Factory function to create a berserker"""
    return Berserker()


# ===== BERSERKER SKILLS =====

class Bloodlust(Skill):
    def __init__(self):
        super().__init__("Bloodlust", "Increases attack speed by 75% for 4 seconds")
        self.cast_time = 0.25
        self.mana_cost = 70
        self.range = 0
        self.duration = 4.0
        self.attack_speed_bonus = 75
        
    def should_cast(self, caster) -> bool:
        return not any(e.name == "Bloodlust" for e in caster.status_effects)
        
    def execute(self, caster):
        effect = StatModifierEffect("Bloodlust", self.duration, {"attack_speed": self.attack_speed_bonus})
        effect.source = caster
        caster.add_status_effect(effect)


def create_berserker_skill(skill_name: str) -> Skill:
    """Create berserker-specific skills"""
    skill_classes = {
        "bloodlust": Bloodlust,
    }
    
    skill_class = skill_classes.get(skill_name.lower())
    if skill_class:
        return skill_class()
    return None