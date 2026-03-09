from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill


class MassOfTentacles(Unit):
    def __init__(self):
        super().__init__("Mass of Tentacles", UnitType.MASS_OF_TENTACLES)
        self.max_hp = 1300
        self.hp = self.max_hp
        self.attack_damage = 60
        self.attack_range = 1
        self.attack_speed = -10
        self.armor = 35
        self.magic_resist = 35
        self.attack_damage_types = [DamageType.PHYSICAL]
        self.immobile = True
        self.affinities = {
            DamageType.ARCANE: ElementalAffinity.STRONG,
            DamageType.PHYSICAL: ElementalAffinity.STRONG,
            DamageType.DARK: ElementalAffinity.STRONG,
            DamageType.HOLY: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(TentacleGrab())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_mass_of_tentacles() -> MassOfTentacles:
    return MassOfTentacles()


class DamageAuraPassive(Skill):
    """Arcane and Dark damage aura."""
    def __init__(self):
        super().__init__("Eldritch Aura", "Deal arcane and dark damage to nearby enemies each second")
        self.is_passive = True
        self.timer = 0
        self.dps = 15

    def update(self, dt):
        if not self.owner or not self.owner.is_alive():
            return
        self.timer += dt
        if self.timer >= 1.0:
            self.timer -= 1.0
            enemies = self.owner.board.get_enemy_units(self.owner.team)
            for enemy in enemies:
                if enemy.is_alive() and self.owner.board.get_distance(self.owner, enemy) <= 2:
                    enemy.take_damage(self.dps, [DamageType.ARCANE, DamageType.DARK], self.owner)


class TentacleGrab(Skill):
    def __init__(self):
        super().__init__("Tentacle", "Pull a unit towards self")
        self.cast_time = 0.3
        self.mana_cost = 60
        self.range = 5
        self.passive = DamageAuraPassive()

    def should_cast(self, caster) -> bool:
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        # Only cast if enemies are far away (no point pulling melee targets)
        far_enemies = [e for e in enemies if caster.board.get_distance(caster, e) > 1]
        return len(far_enemies) > 0

    def execute(self, caster):
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        far_enemies = [e for e in enemies if caster.board.get_distance(caster, e) > 1]
        if not far_enemies:
            return
        # Pull the farthest enemy
        target = max(far_enemies, key=lambda e: caster.board.get_distance(caster, e))
        self._pull_towards(caster, target, 4)
        caster.board.make_text_floater("Grabbed!", (150, 50, 200), unit=target)

    def _pull_towards(self, caster, target, distance):
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
