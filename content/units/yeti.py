import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
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
        self.set_spell(DeepFreeze())

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
