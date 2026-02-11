import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
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

    def get_available_passive_skills(self) -> list:
        return [
            PassiveSkill.MIRROR_IMAGE,
            PassiveSkill.ARCANE_BLADE,
            PassiveSkill.SPELL_SHIELD
        ]

    def get_passive_skill_cost(self, skill_name) -> int:
        costs = {
            PassiveSkill.MIRROR_IMAGE: 50,
            PassiveSkill.ARCANE_BLADE: 35,
            PassiveSkill.SPELL_SHIELD: 40,
        }
        return costs.get(skill_name, 30)

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


class MirrorImage(Skill):
    """Start of battle: Summon 2 copies of self with items"""
    def __init__(self):
        super().__init__("Mirror Image", "Start of battle: Summon 2 copies of self (with items)")
        self.is_passive = True
        self.skill_enum = PassiveSkill.MIRROR_IMAGE
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.triggered = False

    def on_event(self, event_type: str, **kwargs):
        # Trigger at first combat frame
        owner = getattr(self, 'owner', None)
        if not self.triggered and owner and owner.is_alive() and owner.board:
            self.triggered = True
            self.summon_copies()

    def summon_copies(self):
        owner = self.owner
        if not owner or not owner.board:
            return

        for i in range(2):
            # Find empty position near owner
            position = self._find_nearby_position(owner)
            if not position:
                continue

            # Create copy
            copy = MagicKnight()
            copy.max_hp = int(owner.max_hp * 0.5)  # 50% HP
            copy.hp = copy.max_hp
            copy.attack_damage = int(owner.attack_damage * 0.5)  # 50% damage
            copy.is_summoned = True
            copy.summoner = owner

            # Copy items
            for item in owner.items:
                from content.items import create_item
                # Create a copy of the item by name
                item_name = item.name.lower().replace(" ", "_")
                new_item = create_item(item_name)
                if new_item:
                    copy.add_item(new_item)

            # Place on board
            owner.board.add_unit(copy, position[0], position[1], owner.team)

    def _find_nearby_position(self, unit):
        """Find an empty position near the unit"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                x, y = unit.x + dx, unit.y + dy
                if 0 <= x < 8 and 0 <= y < 8:
                    if not unit.board.get_unit_at(x, y):
                        # Check if position is on correct side
                        if unit.team == "player" and x < 4:
                            return (x, y)
                        elif unit.team == "enemy" and x >= 4:
                            return (x, y)
        return None

    def reset(self):
        self.triggered = False


class ArcaneBlade(Skill):
    """Attacks deal bonus magic damage equal to intelligence"""
    def __init__(self):
        super().__init__("Arcane Blade", "Attacks deal bonus magic damage equal to intelligence")
        self.is_passive = True
        self.skill_enum = PassiveSkill.ARCANE_BLADE
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_attack" and kwargs.get("attacker") == owner:
            target = kwargs.get("target")
            if target and target.is_alive() and owner:
                magic_damage = owner.intelligence
                target.take_damage(magic_damage, "magical", owner)


class SpellShield(Skill):
    """Take 30% reduced magic damage"""
    def __init__(self):
        super().__init__("Spell Shield", "Take 30% reduced magic damage")
        self.is_passive = True
        self.skill_enum = PassiveSkill.SPELL_SHIELD
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

    def apply_to_owner(self, owner):
        owner.magic_resist += 43  # ~30% reduction at base


def create_magic_knight_skill(skill_name) -> Skill:
    skill_classes = {
        "arcane_shield": ArcaneShield,
        PassiveSkill.MIRROR_IMAGE: MirrorImage,
        PassiveSkill.ARCANE_BLADE: ArcaneBlade,
        PassiveSkill.SPELL_SHIELD: SpellShield,
    }

    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)

    if skill_class:
        return skill_class()
    return None
