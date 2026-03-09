from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from status_effect import StatModifierEffect
from visual_effect import VisualEffectType
import random


class ImpTorturer(Unit):
    def __init__(self):
        super().__init__("Imp Torturer", UnitType.IMP_TORTURER)
        self.max_hp = 450
        self.hp = self.max_hp
        self.attack_damage = 45
        self.attack_range = 1
        self.attack_speed = 30  # Fast attacks
        self.move_speed = 3.0   # Fast movement
        self.armor = 10
        self.magic_resist = 10
        self.attack_damage_types = [DamageType.PHYSICAL]
        self.affinities = {
            DamageType.DARK: ElementalAffinity.IMMUNE,
            DamageType.FIRE: ElementalAffinity.STRONG,
            DamageType.ICE: ElementalAffinity.VULNERABLE,
            DamageType.HOLY: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(Sparks())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_imp_torturer() -> ImpTorturer:
    return ImpTorturer()


class MicroStunPassive(Skill):
    """On damaging an enemy, stun for 0.1s."""
    def __init__(self):
        super().__init__("Torment", "On damaging an enemy, stun for 0.1s")
        self.is_passive = True

    def on_event(self, event_type, **kwargs):
        if event_type == "damage_taken" and kwargs.get("source") == self.owner:
            target = kwargs.get("unit")
            if target and target.is_alive():
                stun = StatModifierEffect("Tormented", 0.1, {"attack_speed": -9999, "move_speed": -9999})
                stun.source = self.owner
                target.add_status_effect(stun)


class Sparks(Skill):
    def __init__(self):
        super().__init__("Sparks", "Deal fire damage to 3 random enemies")
        self.cast_time = 0.3
        self.mana_cost = 60
        self.range = 6
        self.damage = 80
        self.passive = MicroStunPassive()

    def should_cast(self, caster) -> bool:
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        return len(enemies) > 0

    def execute(self, caster):
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        if not enemies:
            return
        targets = random.sample(enemies, min(3, len(enemies)))
        damage = self.damage * (1 + caster.intelligence / 100)
        for target in targets:
            from projectile import Projectile
            proj = Projectile(caster, target, speed=20.0)
            proj.damage = damage
            proj.damage_types = [DamageType.FIRE]
            proj.on_hit_callback = lambda tgt, d=damage: tgt.take_damage(d, [DamageType.FIRE], caster)
            caster.board.add_projectile(proj)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
