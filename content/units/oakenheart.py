from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from status_effect import StatModifierEffect


class Oakenheart(Unit):
    def __init__(self):
        super().__init__("Oakenheart", UnitType.OAKENHEART)
        self.max_hp = 1400
        self.hp = self.max_hp
        self.attack_damage = 50
        self.attack_range = 1
        self.attack_speed = -20  # Slow attacks
        self.move_speed = 1.5     # Slow movement
        self.armor = 40
        self.magic_resist = 25
        self.attack_damage_types = [DamageType.PHYSICAL]
        self.affinities = {
            DamageType.HOLY: ElementalAffinity.STRONG,
            DamageType.PHYSICAL: ElementalAffinity.STRONG,
            DamageType.POISON: ElementalAffinity.VULNERABLE,
            DamageType.FIRE: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(Entangle())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_oakenheart() -> Oakenheart:
    return Oakenheart()


class ArmorAuraPassive(Skill):
    """Nearby allies gain 1 armor each second."""
    def __init__(self):
        super().__init__("Bark Aura", "Nearby allies gain 1 armor per second")
        self.is_passive = True
        self.timer = 0

    def update(self, dt):
        if not self.owner or not self.owner.is_alive():
            return
        self.timer += dt
        if self.timer >= 1.0:
            self.timer -= 1.0
            allies = self.owner.board.get_allied_units(self.owner.team)
            for ally in allies:
                if ally.is_alive() and ally != self.owner:
                    if self.owner.board.get_distance(self.owner, ally) <= 2:
                        armor_buff = StatModifierEffect("Bark", None, {"armor": 1})
                        armor_buff.source = self.owner
                        ally.add_status_effect(armor_buff)


class Entangle(Skill):
    def __init__(self):
        super().__init__("Entangle", "Stun the highest DPS enemy for 2s")
        self.cast_time = 0.5
        self.mana_cost = 90
        self.range = 5
        self.passive = ArmorAuraPassive()

    def should_cast(self, caster) -> bool:
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        return len(enemies) > 0

    def execute(self, caster):
        enemies = self.get_valid_targets(caster, "enemy", self.range)
        if not enemies:
            return
        # Find highest DPS enemy (attack_damage * attack_speed proxy)
        target = max(enemies, key=lambda e: e.attack_damage * (1 + e.attack_speed / 100))
        stun = StatModifierEffect("Entangled", 2.0, {"attack_speed": -9999, "move_speed": -9999})
        stun.source = caster
        target.add_status_effect(stun)
        caster.board.make_text_floater("Entangled!", (100, 200, 50), unit=target)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)
