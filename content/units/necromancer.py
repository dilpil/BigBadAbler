import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from visual_effect import VisualEffectType

class Necromancer(Unit):
    def __init__(self):
        super().__init__("Necromancer", UnitType.NECROMANCER)
        self.max_hp = 650
        self.hp = self.max_hp
        self.max_mp = 90
        self.mp = 0
        self.attack_damage = 45
        self.attack_range = 4
        self.attack_speed = -20  # 0.8 attacks per second
        self.intelligence = 20
        self.armor = 25
        self.magic_resist = 25
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_necromancer_skill("summon_skeleton")
        if default_skill:
            self.set_spell(default_skill)
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_necromancer() -> Necromancer:
    """Factory function to create a necromancer"""
    return Necromancer()


# ===== NECROMANCER SKILLS =====

class SummonSkeleton(Skill):
    def __init__(self):
        super().__init__("Summon Skeleton", "Summons a skeleton warrior (350 HP, 35 damage) to fight for you")
        self.cast_time = 0.25
        self.mana_cost = 90
        self.summon_type = "skeleton"
        
    def should_cast(self, caster) -> bool:
        return len([u for u in caster.board.player_units if u.unit_type == UnitType.SKELETON]) < 3
        
    def execute(self, caster):
        pos = self.find_summon_position(caster)
        if pos:
            skeleton = self.create_summon(caster)

            # Use the summoning helper
            self.summon_minion(caster, skeleton, pos)

            # Add dark visual effect at the summoning location
            caster.board.add_visual_effect(VisualEffectType.DARK, pos[0], pos[1])
            
    def create_summon(self, caster):
        # Create skeleton with proper enum type
        skeleton = Unit("Skeleton", UnitType.SKELETON)
        skeleton.max_hp = 350
        skeleton.hp = skeleton.max_hp
        skeleton.attack_damage = 35
        skeleton.attack_speed = 0  # 1.0 attacks per second
        skeleton.armor = 20
        return skeleton


def create_necromancer_skill(skill_identifier) -> Skill:
    """Create necromancer-specific skills"""
    skill_classes = {
        "summon_skeleton": SummonSkeleton,
    }
    
    skill_class = skill_classes.get(skill_identifier)
    if skill_class:
        return skill_class()
    return None