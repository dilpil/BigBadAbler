from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from status_effect import StatusEffect, StackType


class CrazedThornhound(Unit):
    def __init__(self):
        super().__init__("Crazed Thornhound", UnitType.CRAZED_THORNHOUND)
        self.max_hp = 800
        self.hp = self.max_hp
        self.attack_damage = 65
        self.attack_range = 1
        self.attack_speed = 10
        self.armor = 20
        self.magic_resist = 15
        self.attack_damage_types = [DamageType.PHYSICAL]
        self.affinities = {
            DamageType.LIGHTNING: ElementalAffinity.STRONG,
            DamageType.FIRE: ElementalAffinity.STRONG,
            DamageType.POISON: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(Berserk())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_crazed_thornhound() -> CrazedThornhound:
    return CrazedThornhound()


class ThornReflect(Skill):
    """Passive: deal phys damage to units that attack it in melee."""
    def __init__(self):
        super().__init__("Thorns", "Deal 20 physical damage to melee attackers")
        self.is_passive = True
        self.reflect_damage = 20

    def on_event(self, event_type, **kwargs):
        if event_type == "unit_attack" and kwargs.get("target") == self.owner:
            attacker = kwargs.get("attacker")
            if attacker and attacker.is_alive() and attacker.attack_range <= 1:
                attacker.take_damage(self.reflect_damage, [DamageType.PHYSICAL], self.owner)


class Berserk(Skill):
    def __init__(self):
        super().__init__("Berserk", "Gain 5% lifesteal and 15% attack speed")
        self.cast_time = 0.2
        self.mana_cost = 50
        self.range = 0
        # Attach passive
        self.passive = ThornReflect()

    def should_cast(self, caster) -> bool:
        return True

    def execute(self, caster):
        effect = BerserkEffect()
        effect.source = caster
        caster.add_status_effect(effect)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)


class BerserkEffect(StatusEffect):
    def __init__(self):
        super().__init__("Berserk", None, StackType.STACK_INTENSITY)
        self.attack_speed_bonus = 15
        self.lifesteal_percent = 5

    def apply(self, unit):
        super().apply(unit)
        unit.attack_speed += self.attack_speed_bonus

    def remove(self, unit):
        unit.attack_speed -= self.attack_speed_bonus * self.stacks
        super().remove(unit)

    def on_event(self, event_type, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            damage = kwargs.get("damage", 0)
            if damage > 0:
                heal = damage * (self.lifesteal_percent * self.stacks / 100.0)
                self.unit.heal(heal, self.unit)
