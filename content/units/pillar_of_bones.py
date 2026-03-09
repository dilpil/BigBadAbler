from unit import Unit, UnitType, DamageType, ElementalAffinity
from skill import Skill
from visual_effect import VisualEffectType


class PillarOfBones(Unit):
    def __init__(self):
        super().__init__("Pillar of Bones", UnitType.PILLAR_OF_BONES)
        self.max_hp = 1000
        self.hp = self.max_hp
        self.attack_damage = 80
        self.attack_range = 1
        self.attack_speed = -30  # Slow attacks
        self.armor = 40
        self.magic_resist = 20
        self.attack_damage_types = [DamageType.PHYSICAL]
        self.immobile = True
        self.affinities = {
            DamageType.DARK: ElementalAffinity.IMMUNE,
            DamageType.POISON: ElementalAffinity.IMMUNE,
            DamageType.HOLY: ElementalAffinity.VULNERABLE,
        }
        self._set_default_skill()

    def _set_default_skill(self):
        self.set_spell(RaiseSkeleton())

    @staticmethod
    def get_cost() -> int:
        return 50


def create_pillar_of_bones() -> PillarOfBones:
    return PillarOfBones()


class DeathManaPassive(Skill):
    """On any unit death, gain 50 mana."""
    def __init__(self):
        super().__init__("Death Harvest", "On any unit death, gain 50 mana")
        self.is_passive = True

    def on_event(self, event_type, **kwargs):
        if event_type == "unit_death" or event_type == "death":
            if event_type == "death" and self.owner and self.owner.is_alive():
                if self.owner.spell:
                    self.owner.spell.add_mana(50)


class RaiseSkeleton(Skill):
    def __init__(self):
        super().__init__("Raise Skeleton", "Summon a skeleton warrior")
        self.cast_time = 0.25
        self.mana_cost = 80
        self.passive = DeathManaPassive()

    def should_cast(self, caster) -> bool:
        skeletons = [u for u in caster.board.get_allied_units(caster.team)
                     if u.unit_type == UnitType.SKELETON and u.is_alive()]
        return len(skeletons) < 4

    def execute(self, caster):
        pos = self.find_summon_position(caster)
        if pos:
            skeleton = Unit("Skeleton", UnitType.SKELETON)
            skeleton.max_hp = 350
            skeleton.hp = skeleton.max_hp
            skeleton.attack_damage = 35
            skeleton.attack_speed = 0
            skeleton.armor = 20
            skeleton.attack_damage_types = [DamageType.PHYSICAL]
            self.summon_minion(caster, skeleton, pos)
            caster.board.add_visual_effect(VisualEffectType.DARK, pos[0], pos[1])

    def update(self, dt):
        self.passive.owner = self.owner
        self.passive.update(dt)

    def on_event(self, event_type, **kwargs):
        self.passive.on_event(event_type, **kwargs)
