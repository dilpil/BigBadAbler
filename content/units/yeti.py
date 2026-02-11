import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
from skill import Skill
from status_effect import StatusEffect, StatModifierEffect

class Yeti(Unit):
    def __init__(self):
        super().__init__("Yeti", UnitType.YETI)
        self.max_hp = 1000
        self.hp = self.max_hp
        self.attack_damage = 70
        self.attack_range = 1
        self.attack_speed = -40
        self.strength = 30
        self.intelligence = 10
        self.armor = 50
        self.magic_resist = 40

        self._set_default_skill()

    def _set_default_skill(self):
        default_skill = create_yeti_skill("deep_freeze")
        if default_skill:
            self.set_spell(default_skill)

    def get_available_passive_skills(self) -> list:
        return [
            PassiveSkill.FROST_AURA,
            PassiveSkill.PERMAFROST,
            PassiveSkill.ICY_TOUCH
        ]

    def get_passive_skill_cost(self, skill_name) -> int:
        costs = {
            PassiveSkill.FROST_AURA: 45,
            PassiveSkill.PERMAFROST: 40,
            PassiveSkill.ICY_TOUCH: 35,
        }
        return costs.get(skill_name, 30)

    @staticmethod
    def get_cost() -> int:
        return 50

def create_yeti() -> Yeti:
    return Yeti()


# ===== YETI SKILLS =====

class DeepFreeze(Skill):
    """Freeze the nearest 3 enemy units for 2 seconds"""
    def __init__(self):
        super().__init__("Deep Freeze", "Freeze the 3 nearest enemies for 2 seconds")
        self.cast_time = 0.5
        self.mana_cost = 60
        self.freeze_duration = 2.0
        self.target_count = 3

    def should_cast(self, caster) -> bool:
        if not caster.board:
            return False
        enemies = caster.board.get_enemy_units(caster.team)
        return any(e.is_alive() for e in enemies)

    def execute(self, caster):
        if not caster.board:
            return

        enemies = caster.board.get_enemy_units(caster.team)
        enemies = [e for e in enemies if e.is_alive()]
        if not enemies:
            return

        # Sort by distance and take nearest 3
        enemies.sort(key=lambda e: caster.board.get_distance(caster, e))
        targets = enemies[:self.target_count]

        for target in targets:
            freeze = FreezeEffect(self.freeze_duration)
            freeze.source = caster
            target.add_status_effect(freeze)

            if caster.board:
                from visual_effect import VisualEffectType
                caster.board.add_visual_effect(VisualEffectType.ICE, target.x, target.y)


class FreezeEffect(StatusEffect):
    """Frozen - cannot act"""
    def __init__(self, duration: float):
        super().__init__("Frozen", duration)
        self.stored_attack_speed = 0
        self.stored_move_speed = 0

    def apply(self, unit):
        # Store original stats and set to extreme negatives
        self.stored_attack_speed = unit.attack_speed
        self.stored_move_speed = unit.move_speed
        unit.attack_speed = -999  # Effectively stops attacking
        unit.move_speed = 0  # Cannot move

    def remove(self, unit):
        # Restore original stats
        unit.attack_speed = self.stored_attack_speed
        unit.move_speed = self.stored_move_speed


class FrostAura(Skill):
    """Passive frost damage aura - enemies within 2 tiles take ice damage"""
    def __init__(self):
        super().__init__("Frost Aura", "Enemies within 2 tiles take 20 ice damage per second")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FROST_AURA
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.damage_per_second = 20
        self.range = 2
        self.tick_timer = 0
        self.tick_interval = 0.5

    def update(self, dt: float):
        super().update(dt)
        owner = getattr(self, 'owner', None)
        if not owner or not owner.is_alive() or not owner.board:
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            damage = self.damage_per_second * self.tick_interval

            enemies = owner.board.get_enemy_units(owner.team)
            for enemy in enemies:
                if enemy.is_alive():
                    distance = owner.board.get_distance(owner, enemy)
                    if distance <= self.range:
                        enemy.take_damage(damage, "ice", owner)


class Permafrost(Skill):
    """Attacks slow enemies by 20% for 3 seconds"""
    def __init__(self):
        super().__init__("Permafrost", "Attacks slow enemies by 20% attack and move speed for 3 seconds")
        self.is_passive = True
        self.skill_enum = PassiveSkill.PERMAFROST
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_attack" and kwargs.get("attacker") == owner:
            target = kwargs.get("target")
            if target and target.is_alive():
                slow = StatModifierEffect("Permafrost", 3.0, {
                    "attack_speed": -20,
                    "move_speed": -0.4
                })
                slow.source = owner
                target.add_status_effect(slow)


class IcyTouch(Skill):
    """Attacks deal bonus ice damage"""
    def __init__(self):
        super().__init__("Icy Touch", "Attacks deal an additional 40 ice damage")
        self.is_passive = True
        self.skill_enum = PassiveSkill.ICY_TOUCH
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.bonus_damage = 40

    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_attack" and kwargs.get("attacker") == owner:
            target = kwargs.get("target")
            if target and target.is_alive():
                target.take_damage(self.bonus_damage, "ice", owner)


def create_yeti_skill(skill_name) -> Skill:
    skill_classes = {
        "deep_freeze": DeepFreeze,
        PassiveSkill.FROST_AURA: FrostAura,
        PassiveSkill.PERMAFROST: Permafrost,
        PassiveSkill.ICY_TOUCH: IcyTouch,
    }

    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)

    if skill_class:
        return skill_class()
    return None
