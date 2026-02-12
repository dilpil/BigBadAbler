import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import StatModifierEffect, StackType

class OgreShaman(Unit):
    def __init__(self):
        super().__init__("Ogre Shaman", UnitType.OGRE_SHAMAN)
        self.max_hp = 900
        self.hp = self.max_hp
        self.attack_damage = 50
        self.attack_range = 1
        self.attack_speed = -30
        self.strength = 25
        self.intelligence = 20
        self.armor = 40
        self.magic_resist = 25

        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(BattleCry())

    @staticmethod
    def get_cost() -> int:
        return 50

def create_ogre_shaman() -> OgreShaman:
    return OgreShaman()


# ===== OGRE SHAMAN SKILLS =====

class BattleCry(Skill):
    """Melee allies get +10% attack speed for rest of battle"""
    def __init__(self):
        super().__init__("Battle Cry", "Melee allies gain +10% attack speed for rest of battle")
        self.cast_time = 0.3
        self.mana_cost = 50
        self.attack_speed_bonus = 10

    def should_cast(self, caster) -> bool:
        if not caster.board:
            return False
        allies = caster.board.get_allied_units(caster.team)
        melee_allies = [a for a in allies if a.is_alive() and a.attack_range <= 1]
        return len(melee_allies) > 0

    def execute(self, caster):
        if not caster.board:
            return

        allies = caster.board.get_allied_units(caster.team)
        for ally in allies:
            if ally.is_alive() and ally.attack_range <= 1:  # Melee units only
                # Permanent buff (no duration)
                buff = StatModifierEffect("Battle Cry", None, {"attack_speed": self.attack_speed_bonus})
                buff.source = caster
                ally.add_status_effect(buff)

                if caster.board:
                    from visual_effect import VisualEffectType
                    caster.board.add_visual_effect(VisualEffectType.HOLY, ally.x, ally.y)
