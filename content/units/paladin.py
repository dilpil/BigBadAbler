import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill

class Paladin(Unit):
    def __init__(self):
        super().__init__("Paladin", UnitType.PALADIN)
        self.max_hp = 850
        self.hp = self.max_hp
        self.max_mp = 60
        self.mp = 0
        self.attack_damage = 60
        self.attack_range = 1
        self.attack_speed = -30  # 0.7 attacks per second
        self.strength = 15
        self.armor = 45
        self.magic_resist = 45
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_paladin_skill("holy_aura")
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

def create_paladin() -> Paladin:
    """Factory function to create a paladin"""
    return Paladin()


# ===== PALADIN SKILLS =====

class HolyAura(Skill):
    def __init__(self):
        super().__init__("Holy Aura", "Heals nearby allies every second")
        self.heal_amount = 30.0
        self.range = 2
        self.tick_timer = 0
        
    def update(self, dt: float):
        super().update(dt)
        if not self.owner or not self.owner.is_alive():
            return
            
        self.tick_timer += dt
        if self.tick_timer >= 1.0:
            self.tick_timer -= 1.0
            allies = self.owner.board.get_units_in_range(self.owner.x, self.owner.y, self.range, self.owner.team)
            for ally in allies:
                if ally.is_alive():
                    ally.heal(self.heal_amount, self.owner)


def create_paladin_skill(skill_name: str) -> Skill:
    """Create paladin-specific skills"""
    skill_classes = {
        "holy_aura": HolyAura,
    }
    
    skill_class = skill_classes.get(skill_name.lower())
    if skill_class:
        return skill_class()
    return None