from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from status_effect import StatusEffect, AbsorbShieldEffect
from visual_effect import VisualEffectType


class SunSpirit(Unit):
    def __init__(self):
        super().__init__("Sun Spirit", UnitType.SUN_SPIRIT)
        self.max_hp = 1200
        self.hp = self.max_hp
        self.attack_damage = 40
        self.attack_range = 1
        self.attack_speed = 0
        self.armor = 30
        self.magic_resist = 30
        self.attack_damage_types = [DamageType.FIRE]
        self.affinities = {
            DamageType.HOLY: ElementalAffinity.IMMUNE,
            DamageType.FIRE: ElementalAffinity.STRONG,
            DamageType.DARK: ElementalAffinity.STRONG,
            DamageType.PHYSICAL: ElementalAffinity.STRONG,
            DamageType.ICE: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(FireShield())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_sun_spirit() -> SunSpirit:
    return SunSpirit()


class FireShieldEffect(StatusEffect):
    """Shield that deals fire damage to nearby enemies while active."""
    def __init__(self, shield_amount, dps):
        super().__init__("Fire Shield", None)
        self.shield_remaining = shield_amount
        self.dps = dps
        self.tick_interval = 0.5

    def apply(self, unit):
        super().apply(unit)

    def on_tick(self):
        if not self.unit or not self.unit.is_alive():
            return
        if self.shield_remaining <= 0:
            return
        # Deal fire damage to nearby enemies
        enemies = self.unit.board.get_enemy_units(self.unit.team)
        for enemy in enemies:
            if enemy.is_alive() and self.unit.board.get_distance(self.unit, enemy) <= 2:
                enemy.take_damage(self.dps * self.tick_interval, [DamageType.FIRE], self.unit)

    def on_event(self, event_type, **kwargs):
        if event_type == "damage_taken" and kwargs.get("unit") == self.unit:
            damage = kwargs.get("damage", 0)
            self.shield_remaining -= damage
            if self.shield_remaining <= 0:
                self.shield_remaining = 0
                # Remove the effect
                if self.unit:
                    self.unit.remove_status_effect(self)


class SunSpiritPassive(Skill):
    """Nearby allies heal each second."""
    def __init__(self):
        super().__init__("Radiance", "Nearby allies heal 15 HP per second")
        self.is_passive = True
        self.heal_timer = 0
        self.heal_per_sec = 15

    def update(self, dt):
        if not self.owner or not self.owner.is_alive():
            return
        self.heal_timer += dt
        if self.heal_timer >= 1.0:
            self.heal_timer -= 1.0
            allies = self.owner.board.get_allied_units(self.owner.team)
            for ally in allies:
                if ally.is_alive() and ally != self.owner:
                    if self.owner.board.get_distance(self.owner, ally) <= 2:
                        ally.heal(self.heal_per_sec, self.owner)


class FireShield(Skill):
    def __init__(self):
        super().__init__("Fire Shield", "Gain 200[holy] HP shield. While active, deal 10[fire] damage/s to nearby enemies")
        self.cast_time = 0.3
        self.mana_cost = 80
        self.range = 0
        # Attach passive
        self.passive = SunSpiritPassive()

    def should_cast(self, caster) -> bool:
        # Cast when no active fire shield
        for effect in caster.status_effects:
            if effect.name == "Fire Shield" and effect.shield_remaining > 0:
                return False
        return True

    def execute(self, caster):
        shield = FireShieldEffect(200 * (1 + caster.intelligence / 100), 10 * (1 + caster.intelligence / 100))
        shield.source = caster
        caster.add_status_effect(shield)
        caster.board.add_visual_effect(VisualEffectType.HOLY, caster.x, caster.y)

    def update(self, dt):
        # Delegate to passive
        self.passive.owner = self.owner
        self.passive.update(dt)
