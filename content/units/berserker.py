import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType

class Berserker(Unit):
    def __init__(self):
        super().__init__("Berserker", UnitType.BERSERKER)
        self.max_hp = 120
        self.hp = self.max_hp
        self.max_mp = 60
        self.mp = self.max_mp
        self.attack_damage = 20
        self.attack_range = 1
        self.strength = 25
        self.attack_speed = 20
        self.armor = 15
        self.magic_resist = 10
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        from content.skills import create_skill
        default_skill = create_skill("bloodlust")
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