import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType

class Necromancer(Unit):
    def __init__(self):
        super().__init__("Necromancer", UnitType.NECROMANCER)
        self.max_hp = 80
        self.hp = self.max_hp
        self.max_mp = 120
        self.mp = self.max_mp
        self.attack_damage = 8
        self.attack_range = 4
        self.intelligence = 20
        self.armor = 5
        self.magic_resist = 15
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        from content.skills import create_skill
        default_skill = create_skill("summon_skeleton")
        if default_skill:
            self.set_spell(default_skill)
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return [
            "hunger",
            "bone_shards", 
            "undead_horde",
            "burning_bones",
            "grave_chill",
            "bone_fragments",
            "bone_sabers"
        ]
    
    def get_passive_skill_cost(self, skill_name: str) -> int:
        """Get the cost of a passive skill"""
        costs = {
            "hunger": 35,
            "bone_shards": 30,
            "undead_horde": 45,
            "burning_bones": 40,
            "grave_chill": 35,
            "bone_fragments": 30,
            "bone_sabers": 25,
        }
        return costs.get(skill_name, 30)
    
    def get_available_skills(self) -> list:
        """Get list of available active skills for this unit"""
        return ["summon_skeleton", "raise_dead", "life_drain", "death_coil", 
                "bone_armor", "unholy_presence", "corpse_explosion", "dark_ritual", "plague"]
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_necromancer() -> Necromancer:
    """Factory function to create a necromancer"""
    return Necromancer()