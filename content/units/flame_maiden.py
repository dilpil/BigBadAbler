from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from visual_effect import VisualEffectType


class FlameMaiden(Unit):
    def __init__(self):
        super().__init__("Flame Maiden", UnitType.FLAME_MAIDEN)
        self.max_hp = 650
        self.hp = self.max_hp
        self.attack_damage = 40
        self.attack_range = 4
        self.attack_speed = 0
        self.armor = 15
        self.magic_resist = 20
        self.intelligence = 15
        self.attack_damage_types = [DamageType.FIRE]
        self.affinities = {
            DamageType.FIRE: ElementalAffinity.IMMUNE,
            DamageType.PHYSICAL: ElementalAffinity.STRONG,
            DamageType.ICE: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(FlameBlast())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_flame_maiden() -> FlameMaiden:
    return FlameMaiden()


class FireChargePassive(Skill):
    """On enemy takes fire damage, gain a charge. At 25 charges, heal lowest HP ally."""
    def __init__(self):
        super().__init__("Ember Soul", "On fire damage dealt, gain charge. At 25, heal lowest ally")
        self.is_passive = True
        self.charges = 0
        self.charge_threshold = 25

    def on_event(self, event_type, **kwargs):
        if event_type == "damage_taken" and kwargs.get("source") == self.owner:
            damage_types = kwargs.get("damage_types", [])
            if DamageType.FIRE in damage_types:
                damage = kwargs.get("damage", 0)
                self.charges += damage
                while self.charges >= self.charge_threshold:
                    self.charges -= self.charge_threshold
                    self._heal_lowest_ally()

    def _heal_lowest_ally(self):
        if not self.owner or not self.owner.board:
            return
        allies = self.owner.board.get_allied_units(self.owner.team)
        alive_allies = [a for a in allies if a.is_alive()]
        if alive_allies:
            target = min(alive_allies, key=lambda a: a.hp / a.max_hp)
            heal = self.charge_threshold * (1 + self.owner.intelligence / 100)
            target.heal(heal, self.owner)
            self.owner.board.make_text_floater("Ember Heal!", (255, 150, 50), unit=target)


class FlameBlast(Skill):
    def __init__(self):
        super().__init__("Flame Blast", "Deal fire damage in a 2 tile radius around target")
        self.cast_time = 0.5
        self.mana_cost = 80
        self.range = 5
        self.damage = 100
        self.passive = FireChargePassive()

    def should_cast(self, caster) -> bool:
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        return len(enemies) > 0

    def execute(self, caster):
        # Target the current target or nearest enemy
        target = caster.target if caster.target and caster.target.is_alive() else None
        if not target:
            enemies = self.get_valid_targets(caster, "enemy", self.range)
            if enemies:
                target = enemies[0]
        if not target:
            return

        damage = self.damage * (1 + caster.intelligence / 100)
        # Hit all enemies within 2 tiles of target
        enemies_in_area = self.get_targets_in_area(caster, target.x, target.y, 2, "enemy")
        for enemy in enemies_in_area:
            enemy.take_damage(damage, [DamageType.FIRE], caster)
        caster.board.add_visual_effect(VisualEffectType.FIRE, target.x, target.y)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
