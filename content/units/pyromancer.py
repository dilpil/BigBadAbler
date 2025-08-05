import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from projectile import AoEProjectile

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
        default_skill = create_pyromancer_skill("fireball")
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

def create_pyromancer() -> Pyromancer:
    """Factory function to create a pyromancer"""
    return Pyromancer()


# ===== PYROMANCER SKILLS =====

class Fireball(Skill):
    def __init__(self):
        super().__init__("Fireball", "Launches an explosive fireball at the nearest enemy")
        self.cast_time = 0.8
        self.mana_cost = 100
        self.range = 6
        self.aoe_radius = 2
        self.damage = 40
        
    def should_cast(self, caster) -> bool:
        return len(self.get_valid_targets(caster, "enemy")) > 0
        
    def execute(self, caster):
        targets = self.get_valid_targets(caster, "enemy")
        if targets:
            target = targets[0]  # Use first valid target
            projectile = AoEProjectile(caster, target.x, target.y, speed=8.0)
            projectile.damage = self.damage * (1 + caster.intelligence / 100)
            projectile.damage_type = "magical"
            projectile.explosion_radius = self.aoe_radius
            caster.board.add_projectile(projectile)


def create_pyromancer_skill(skill_name: str) -> Skill:
    """Create pyromancer-specific skills"""
    skill_classes = {
        "fireball": Fireball,
    }
    
    skill_class = skill_classes.get(skill_name.lower())
    if skill_class:
        return skill_class()
    return None