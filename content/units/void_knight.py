from unit import Unit, UnitType, UnitState, DamageType, ElementalAffinity
from skill import Skill
from status_effect import AbsorbShieldEffect
import random


class VoidKnight(Unit):
    def __init__(self):
        super().__init__("Void Knight", UnitType.VOID_KNIGHT)
        self.max_hp = 900
        self.hp = self.max_hp
        self.attack_damage = 60
        self.attack_range = 1
        self.attack_speed = 10
        self.armor = 30
        self.magic_resist = 25
        self.attack_damage_types = [DamageType.ARCANE]
        self.affinities = {
            DamageType.ARCANE: ElementalAffinity.STRONG,
            DamageType.PHYSICAL: ElementalAffinity.STRONG,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(VoidStrike())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_void_knight() -> VoidKnight:
    return VoidKnight()


class ArcaneShieldPassive(Skill):
    """On deal arcane damage, gain 20% of dealt damage as shield for 5s."""
    def __init__(self):
        super().__init__("Void Shield", "On deal arcane damage, gain 20% as shield for 5s")
        self.is_passive = True

    def on_event(self, event_type, **kwargs):
        if event_type == "damage_taken" and kwargs.get("source") == self.owner:
            damage_types = kwargs.get("damage_types", [])
            if DamageType.ARCANE in damage_types:
                damage = kwargs.get("damage", 0)
                shield_amount = damage * 0.2
                if shield_amount > 0 and self.owner:
                    shield = AbsorbShieldEffect("Void Shield", 5.0, shield_amount)
                    shield.source = self.owner
                    self.owner.add_status_effect(shield)


class VoidStrike(Skill):
    def __init__(self):
        super().__init__("Void Strike", "Cleanse debuffs, drop aggro, teleport to random target and attack")
        self.cast_time = 0.2
        self.mana_cost = 80
        self.range = 8
        self.passive = ArcaneShieldPassive()

    def should_cast(self, caster) -> bool:
        enemies = self.get_valid_targets(caster, "enemy", 8)
        return len(enemies) > 0

    def execute(self, caster):
        # Cleanse all debuffs
        for effect in caster.status_effects[:]:
            effect.remove(caster)
        caster.status_effects.clear()

        # Drop aggro - clear all enemies targeting this unit
        enemies = caster.board.get_enemy_units(caster.team)
        for enemy in enemies:
            if enemy.target == caster:
                enemy.target = None

        # Teleport to random enemy
        alive_enemies = [e for e in enemies if e.is_alive()]
        if not alive_enemies:
            return
        target = random.choice(alive_enemies)

        # Find adjacent position to target
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            new_x, new_y = target.x + dx, target.y + dy
            if caster.board.is_valid_position(new_x, new_y) and not caster.board.get_unit_at(new_x, new_y):
                caster.board.move_unit(caster, new_x, new_y)
                break

        # Attack the target
        caster.target = target
        damage = caster.attack_damage * (1 + caster.strength / 100) * 1.5
        target.take_damage(damage, [DamageType.ARCANE], caster)
        caster.board.make_text_floater("Void Strike!", (100, 150, 255), unit=target)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
