import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import StatusEffect

class MagicKnight(Unit):
    def __init__(self):
        super().__init__("Magic Knight", UnitType.MAGIC_KNIGHT)
        self.max_hp = 700
        self.hp = self.max_hp
        self.attack_damage = 55
        self.attack_range = 1
        self.attack_speed = 0
        self.strength = 20
        self.intelligence = 30
        self.armor = 35
        self.magic_resist = 35

        self._set_default_skill()

    def _set_default_skill(self):
        default_skill = create_magic_knight_skill("arcane_shield")
        if default_skill:
            self.set_spell(default_skill)

    @staticmethod
    def get_cost() -> int:
        return 50

def create_magic_knight() -> MagicKnight:
    return MagicKnight()


# ===== MAGIC KNIGHT SKILLS =====

class ArcaneShield(Skill):
    """Give self and all allies within 2 tiles a shield that blocks 200 HP for 6 seconds"""
    def __init__(self):
        super().__init__("Arcane Shield", "Shield self and allies within 2 tiles for 200 HP for 6 seconds")
        self.cast_time = 0.3
        self.mana_cost = 50
        self.shield_amount = 200
        self.shield_duration = 6.0
        self.range = 2

    def should_cast(self, caster) -> bool:
        return caster.board is not None

    def execute(self, caster):
        if not caster.board:
            return
        allies = caster.board.get_units_in_range(caster.x, caster.y, self.range, caster.team)
        for ally in allies:
            if ally.is_alive():
                shield = ShieldEffect(self.shield_amount, self.shield_duration)
                shield.source = caster
                ally.add_status_effect(shield)
                if caster.board:
                    from visual_effect import VisualEffectType
                    caster.board.add_visual_effect(VisualEffectType.HOLY, ally.x, ally.y)


class ShieldEffect(StatusEffect):
    """A shield that absorbs damage"""
    def __init__(self, amount: float, duration: float):
        super().__init__("Arcane Shield", duration)
        self.shield_amount = amount
        self.remaining_shield = amount

    def on_damage_taken(self, unit, damage_amount: float, damage_type: str, source) -> float:
        """Intercept damage and absorb it"""
        if self.remaining_shield <= 0:
            return damage_amount

        absorbed = min(damage_amount, self.remaining_shield)
        self.remaining_shield -= absorbed

        if self.remaining_shield <= 0:
            unit.remove_status_effect(self)

        return damage_amount - absorbed


def create_magic_knight_skill(skill_name) -> Skill:
    skill_classes = {
        "arcane_shield": ArcaneShield,
    }

    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)

    if skill_class:
        return skill_class()
    return None
