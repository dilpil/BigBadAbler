import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType

class Pyromancer(Unit):
    def __init__(self):
        super().__init__("Pyromancer", UnitType.PYROMANCER)
        self.max_hp = 70
        self.hp = self.max_hp
        self.max_mp = 140
        self.mp = self.max_mp
        self.attack_damage = 6
        self.attack_range = 5
        self.intelligence = 30
        self.armor = 5
        self.magic_resist = 10
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        from content.skills import create_skill
        default_skill = create_skill("fireball")
        if default_skill:
            self.set_spell(default_skill)
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return []  # No passive skills yet
    
    def get_passive_skill_cost(self, skill_name: str) -> int:
        """Get the cost of a passive skill"""
        return 30  # Default cost
    
    def get_available_skills(self) -> list:
        """Get list of available active skills for this unit"""
        return ["fireball", "flame_burst", "meteor", "fire_wall", 
                "inferno", "flame_shield", "phoenix", "blazing_orb", "scorch"]
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_pyromancer() -> Pyromancer:
    """Factory function to create a pyromancer"""
    return Pyromancer()