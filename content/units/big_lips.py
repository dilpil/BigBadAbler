from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from status_effect import AbsorbShieldEffect


class BigLips(Unit):
    def __init__(self):
        super().__init__("Big Lips", UnitType.BIG_LIPS)
        self.max_hp = 500
        self.hp = self.max_hp
        self.attack_damage = 40
        self.attack_range = 4
        self.attack_speed = 10
        self.armor = 10
        self.magic_resist = 15
        self.move_speed = 3.0
        self.attack_damage_types = [DamageType.ARCANE]
        self.affinities = {
            DamageType.ARCANE: ElementalAffinity.IMMUNE,
            DamageType.POISON: ElementalAffinity.STRONG,
            DamageType.HOLY: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(TongueAttack())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_big_lips() -> BigLips:
    return BigLips()


class AllyShieldPassive(Skill):
    """Allies within 2 tiles start battle with a 25% Max HP shield."""
    def __init__(self):
        super().__init__("Protective Aura", "Allies within 2 tiles start with 25% Max HP shield")
        self.is_passive = True
        self.applied = False

    def on_event(self, event_type, **kwargs):
        if not self.applied and self.owner and self.owner.board:
            # Apply shields on first event (battle has started)
            self.applied = True
            allies = self.owner.board.get_allied_units(self.owner.team)
            for ally in allies:
                if ally != self.owner and ally.is_alive():
                    if self.owner.board.get_distance(self.owner, ally) <= 2:
                        shield_amount = ally.max_hp * 0.25
                        shield = AbsorbShieldEffect("Protective Shield", 30.0, shield_amount)
                        shield.source = self.owner
                        ally.add_status_effect(shield)


class TongueAttack(Skill):
    def __init__(self):
        super().__init__("Tongue Attack", "Deal phys damage and pull farthest enemies 3 tiles closer")
        self.cast_time = 0.4
        self.mana_cost = 70
        self.range = 6
        self.passive = AllyShieldPassive()

    def should_cast(self, caster) -> bool:
        enemies = self.get_valid_targets(caster, "enemy", 8)
        return len(enemies) > 0

    def execute(self, caster):
        enemies = self.get_valid_targets(caster, "enemy", 8)
        if not enemies:
            return
        # Sort by distance, farthest first
        enemies.sort(key=lambda e: caster.board.get_distance(caster, e), reverse=True)
        # Pull up to 3 farthest enemies
        damage = 50 * (1 + caster.strength / 100)
        for enemy in enemies[:3]:
            enemy.take_damage(damage, [DamageType.PHYSICAL], caster)
            self._pull_towards(caster, enemy, 3)

    def _pull_towards(self, caster, target, distance):
        """Pull target towards caster by up to distance tiles."""
        for _ in range(distance):
            dx = caster.x - target.x
            dy = caster.y - target.y
            if dx == 0 and dy == 0:
                break
            move_x = (1 if dx > 0 else -1) if dx != 0 else 0
            move_y = (1 if dy > 0 else -1) if dy != 0 else 0
            new_x = target.x + move_x
            new_y = target.y + move_y
            if caster.board.is_valid_position(new_x, new_y) and not caster.board.get_unit_at(new_x, new_y):
                caster.board.move_unit(target, new_x, new_y)
            else:
                break

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
