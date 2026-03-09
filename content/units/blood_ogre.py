from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from status_effect import StatModifierEffect


class BloodOgre(Unit):
    def __init__(self):
        super().__init__("Blood Ogre", UnitType.BLOOD_OGRE)
        self.max_hp = 1400
        self.hp = self.max_hp
        self.attack_damage = 70
        self.attack_range = 1
        self.attack_speed = 0
        self.armor = 35
        self.magic_resist = 20
        self.strength = 15
        self.attack_damage_types = [DamageType.PHYSICAL]
        self.affinities = {
            DamageType.DARK: ElementalAffinity.STRONG,
            DamageType.ICE: ElementalAffinity.STRONG,
            DamageType.FIRE: ElementalAffinity.VULNERABLE,
            DamageType.HOLY: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(Crushblow())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_blood_ogre() -> BloodOgre:
    return BloodOgre()


class BattleCryPassive(Skill):
    """On battle start, adjacent allies get +25% attack damage."""
    def __init__(self):
        super().__init__("Battle Cry", "Adjacent allies get +25% attack damage at battle start")
        self.is_passive = True
        self.applied = False

    def on_event(self, event_type, **kwargs):
        if not self.applied and self.owner and self.owner.board:
            self.applied = True
            allies = self.owner.board.get_allied_units(self.owner.team)
            for ally in allies:
                if ally != self.owner and ally.is_alive():
                    if self.owner.board.get_distance(self.owner, ally) <= 1:
                        bonus = int(ally.attack_damage * 0.25)
                        buff = StatModifierEffect("Battle Cry", None, {"attack_damage": bonus})
                        buff.source = self.owner
                        ally.add_status_effect(buff)
                        self.owner.board.make_text_floater("+25% AD!", (255, 100, 100), unit=ally)


class Crushblow(Skill):
    def __init__(self):
        super().__init__("Crushblow", "Hit current target for 500% AD and stun for 2s")
        self.cast_time = 0.5
        self.mana_cost = 100
        self.range = 1
        self.passive = BattleCryPassive()

    def should_cast(self, caster) -> bool:
        return caster.target and caster.target.is_alive() and caster.board.get_distance(caster, caster.target) <= 1

    def execute(self, caster):
        target = caster.target
        if not target or not target.is_alive():
            return
        damage = caster.attack_damage * (1 + caster.strength / 100) * 5.0
        target.take_damage(damage, [DamageType.PHYSICAL], caster)
        stun = StatModifierEffect("Crushed", 2.0, {"attack_speed": -9999, "move_speed": -9999})
        stun.source = caster
        target.add_status_effect(stun)
        caster.board.make_text_floater("CRUSHBLOW!", (255, 50, 50), unit=target)

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
