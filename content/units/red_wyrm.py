from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from visual_effect import VisualEffectType
import random


class RedWyrm(Unit):
    def __init__(self):
        super().__init__("Red Wyrm", UnitType.RED_WYRM)
        self.max_hp = 1500
        self.hp = self.max_hp
        self.attack_damage = 90
        self.attack_range = 1
        self.attack_speed = -30  # Slow attacks
        self.move_speed = 1.5     # Slow movement
        self.armor = 40
        self.magic_resist = 25
        self.strength = 20
        self.attack_damage_types = [DamageType.PHYSICAL]
        self.affinities = {
            DamageType.FIRE: ElementalAffinity.IMMUNE,
            DamageType.PHYSICAL: ElementalAffinity.STRONG,
            DamageType.ICE: ElementalAffinity.VULNERABLE,
            DamageType.POISON: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(FireLine())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_red_wyrm() -> RedWyrm:
    return RedWyrm()


class DisplacePassive(Skill):
    """On attack, displace defender to random adjacent tile and move into that tile."""
    def __init__(self):
        super().__init__("Rampage", "On attack, push defender aside and advance")
        self.is_passive = True

    def on_event(self, event_type, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.owner:
            target = kwargs.get("target")
            if not target or not target.is_alive() or not self.owner.board:
                return
            # Only works in melee range
            if self.owner.board.get_distance(self.owner, target) > 1:
                return
            # Find random adjacent empty tile for target
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            random.shuffle(directions)
            old_x, old_y = target.x, target.y
            for dx, dy in directions:
                new_x, new_y = target.x + dx, target.y + dy
                if (self.owner.board.is_valid_position(new_x, new_y) and
                        not self.owner.board.get_unit_at(new_x, new_y)):
                    self.owner.board.move_unit(target, new_x, new_y)
                    # Move wyrm into the old position
                    self.owner.board.move_unit(self.owner, old_x, old_y)
                    break


class FireLine(Skill):
    def __init__(self):
        super().__init__("Fire Breath", "Deal fire damage in a line towards target")
        self.cast_time = 0.5
        self.mana_cost = 80
        self.range = 5
        self.damage = 120
        self.passive = DisplacePassive()

    def should_cast(self, caster) -> bool:
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        return len(enemies) > 0

    def execute(self, caster):
        target = caster.target if caster.target and caster.target.is_alive() else None
        if not target:
            enemies = self.get_valid_targets(caster, "enemy", self.range)
            if enemies:
                target = enemies[0]
        if not target:
            return

        damage = self.damage * (1 + caster.intelligence / 100)
        # Fire in a line from caster to target
        dx = target.x - caster.x
        dy = target.y - caster.y
        # Normalize direction
        step_x = (1 if dx > 0 else -1) if dx != 0 else 0
        step_y = (1 if dy > 0 else -1) if dy != 0 else 0
        # Hit all enemies along the line for 5 tiles
        for i in range(1, 6):
            check_x = caster.x + step_x * i
            check_y = caster.y + step_y * i
            if not caster.board.is_valid_position(check_x, check_y):
                break
            unit_at = caster.board.get_unit_at(check_x, check_y)
            if unit_at and unit_at.is_alive() and unit_at.team != caster.team:
                unit_at.take_damage(damage, [DamageType.FIRE], caster)
            caster.board.add_visual_effect(VisualEffectType.FIRE, check_x, check_y)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
