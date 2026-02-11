import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
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
        default_skill = create_ogre_shaman_skill("battle_cry")
        if default_skill:
            self.set_spell(default_skill)

    def get_available_passive_skills(self) -> list:
        return [
            PassiveSkill.BLOOD_BOND,
            PassiveSkill.WAR_DRUMS,
            PassiveSkill.TRIBAL_MIGHT
        ]

    def get_passive_skill_cost(self, skill_name) -> int:
        costs = {
            PassiveSkill.BLOOD_BOND: 50,
            PassiveSkill.WAR_DRUMS: 40,
            PassiveSkill.TRIBAL_MIGHT: 35,
        }
        return costs.get(skill_name, 30)

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
                    caster.board.add_visual_effect(VisualEffectType.BUFF, ally.x, ally.y)


class BloodBond(Skill):
    """Start of battle: all adjacent units get +100% max HP"""
    def __init__(self):
        super().__init__("Blood Bond", "Start of battle: adjacent allies gain +100% max HP")
        self.is_passive = True
        self.skill_enum = PassiveSkill.BLOOD_BOND
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.triggered = False

    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if not self.triggered and owner and owner.is_alive() and owner.board:
            self.triggered = True
            self.apply_hp_bonus()

    def apply_hp_bonus(self):
        owner = self.owner
        if not owner or not owner.board:
            return

        allies = owner.board.get_units_in_range(owner.x, owner.y, 1, owner.team)
        for ally in allies:
            if ally != owner and ally.is_alive():
                hp_bonus = ally.max_hp  # +100%
                ally.max_hp += hp_bonus
                ally.hp += hp_bonus

                if owner.board:
                    from visual_effect import VisualEffectType
                    owner.board.add_visual_effect(VisualEffectType.BUFF, ally.x, ally.y)

    def reset(self):
        self.triggered = False


class WarDrums(Skill):
    """Allies gain +5 attack speed each second"""
    def __init__(self):
        super().__init__("War Drums", "All allies gain +5 attack speed every second")
        self.is_passive = True
        self.skill_enum = PassiveSkill.WAR_DRUMS
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.tick_timer = 0
        self.tick_interval = 1.0
        self.attack_speed_per_tick = 5

    def update(self, dt: float):
        super().update(dt)
        owner = getattr(self, 'owner', None)
        if not owner or not owner.is_alive() or not owner.board:
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            allies = owner.board.get_allied_units(owner.team)
            for ally in allies:
                if ally.is_alive():
                    ally.attack_speed += self.attack_speed_per_tick


class TribalMight(Skill):
    """Gain +15 strength and +15 armor"""
    def __init__(self):
        super().__init__("Tribal Might", "+15 strength and +15 armor")
        self.is_passive = True
        self.skill_enum = PassiveSkill.TRIBAL_MIGHT
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

    def apply_to_owner(self, owner):
        owner.strength += 15
        owner.armor += 15


def create_ogre_shaman_skill(skill_name) -> Skill:
    skill_classes = {
        "battle_cry": BattleCry,
        PassiveSkill.BLOOD_BOND: BloodBond,
        PassiveSkill.WAR_DRUMS: WarDrums,
        PassiveSkill.TRIBAL_MIGHT: TribalMight,
    }

    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)

    if skill_class:
        return skill_class()
    return None
