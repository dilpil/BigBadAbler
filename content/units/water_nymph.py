from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill


class WaterNymph(Unit):
    def __init__(self):
        super().__init__("Water Nymph", UnitType.WATER_NYMPH)
        self.max_hp = 700
        self.hp = self.max_hp
        self.attack_damage = 35
        self.attack_range = 4
        self.attack_speed = 0
        self.armor = 10
        self.magic_resist = 30
        self.intelligence = 20
        self.attack_damage_types = [DamageType.ICE]
        self.affinities = {
            DamageType.ARCANE: ElementalAffinity.STRONG,
            DamageType.ICE: ElementalAffinity.STRONG,
            DamageType.FIRE: ElementalAffinity.STRONG,
            DamageType.DARK: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(HealSpell())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_water_nymph() -> WaterNymph:
    return WaterNymph()


class SplashHealPassive(Skill):
    """Autoattacks heal adjacent allies."""
    def __init__(self):
        super().__init__("Splash", "Autoattacks heal adjacent allies for 20 HP")
        self.is_passive = True
        self.heal_amount = 20

    def on_event(self, event_type, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.owner:
            if not self.owner or not self.owner.board:
                return
            allies = self.owner.board.get_allied_units(self.owner.team)
            for ally in allies:
                if ally.is_alive() and ally != self.owner:
                    if self.owner.board.get_distance(self.owner, ally) <= 2:
                        ally.heal(self.heal_amount, self.owner)


class HealSpell(Skill):
    def __init__(self):
        super().__init__("Heal", "Heal lowest HP ally for 200 HP")
        self.cast_time = 0.5
        self.mana_cost = 70
        self.range = 6
        self.heal_amount = 200
        self.passive = SplashHealPassive()

    def should_cast(self, caster) -> bool:
        allies = caster.board.get_allied_units(caster.team)
        injured = [a for a in allies if a.is_alive() and a.hp < a.max_hp * 0.8]
        return len(injured) > 0

    def execute(self, caster):
        allies = caster.board.get_allied_units(caster.team)
        injured = [a for a in allies if a.is_alive()]
        if injured:
            target = min(injured, key=lambda a: a.hp / a.max_hp)
            heal = self.heal_amount * (1 + caster.intelligence / 100)
            target.heal(heal, caster)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
