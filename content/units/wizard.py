import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
from skill import Skill

class Wizard(Unit):
    def __init__(self):
        super().__init__("Wizard", UnitType.WIZARD)
        self.max_hp = 500
        self.hp = self.max_hp
        self.attack_damage = 40
        self.attack_range = 4
        self.attack_speed = -20
        self.strength = 0
        self.intelligence = 50
        self.armor = 15
        self.magic_resist = 30

        self._set_default_skill()

    def _set_default_skill(self):
        default_skill = create_wizard_skill("chain_lightning")
        if default_skill:
            self.set_spell(default_skill)

    def get_available_passive_skills(self) -> list:
        return [
            PassiveSkill.FIRE_SPLASH,
            PassiveSkill.CHAIN_MASTERY,
            PassiveSkill.ARCANE_POWER
        ]

    def get_passive_skill_cost(self, skill_name) -> int:
        costs = {
            PassiveSkill.FIRE_SPLASH: 40,
            PassiveSkill.CHAIN_MASTERY: 35,
            PassiveSkill.ARCANE_POWER: 45,
        }
        return costs.get(skill_name, 30)

    @staticmethod
    def get_cost() -> int:
        return 50

def create_wizard() -> Wizard:
    return Wizard()


# ===== WIZARD SKILLS =====

class ChainLightning(Skill):
    """Chain lightning that hits 5 targets"""
    def __init__(self):
        super().__init__("Chain Lightning", "Lightning bolt chains to 5 enemies, dealing 150 damage each")
        self.cast_time = 0.4
        self.mana_cost = 60
        self.damage = 150
        self.chain_count = 5
        self.chain_range = 3

    def should_cast(self, caster) -> bool:
        if not caster.board:
            return False
        enemies = caster.board.get_enemy_units(caster.team)
        return any(e.is_alive() for e in enemies)

    def execute(self, caster):
        if not caster.board:
            return

        # Get chain mastery bonus
        extra_chains = 0
        for passive in caster.passive_skills:
            if hasattr(passive, 'skill_enum') and passive.skill_enum == PassiveSkill.CHAIN_MASTERY:
                extra_chains = 2
                break

        total_chains = self.chain_count + extra_chains
        damage = self.damage * (1 + caster.intelligence / 100)

        enemies = caster.board.get_enemy_units(caster.team)
        enemies = [e for e in enemies if e.is_alive()]
        if not enemies:
            return

        # Start with nearest enemy
        import random
        hit_enemies = []
        current_target = min(enemies, key=lambda e: caster.board.get_distance(caster, e))

        for _ in range(total_chains):
            if not current_target or current_target in hit_enemies:
                # Find new target not yet hit
                available = [e for e in enemies if e.is_alive() and e not in hit_enemies]
                if not available:
                    break
                current_target = random.choice(available)

            hit_enemies.append(current_target)
            current_target.take_damage(damage, "lightning", caster)

            if caster.board:
                from visual_effect import VisualEffectType
                caster.board.add_visual_effect(VisualEffectType.LIGHTNING, current_target.x, current_target.y)

            # Find next target in chain range
            nearby = [e for e in enemies if e.is_alive() and e not in hit_enemies
                     and caster.board.get_distance(current_target, e) <= self.chain_range]
            if nearby:
                current_target = min(nearby, key=lambda e: caster.board.get_distance(current_target, e))
            else:
                current_target = None


class FireSplash(Skill):
    """Attacks deal AOE fire splash damage"""
    def __init__(self):
        super().__init__("Fire Splash", "Attacks deal fire splash damage to enemies within 1 tile of target")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FIRE_SPLASH
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.splash_damage_percent = 0.5  # 50% of attack damage

    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_attack" and kwargs.get("attacker") == owner:
            target = kwargs.get("target")
            damage = kwargs.get("damage", 0)
            if target and owner and owner.board:
                self.do_splash(owner, target, damage)

    def do_splash(self, owner, primary_target, damage):
        splash_damage = damage * self.splash_damage_percent
        enemies = owner.board.get_enemy_units(owner.team)

        for enemy in enemies:
            if enemy != primary_target and enemy.is_alive():
                distance = owner.board.get_distance(primary_target, enemy)
                if distance <= 1:
                    enemy.take_damage(splash_damage, "fire", owner)
                    if owner.board:
                        from visual_effect import VisualEffectType
                        owner.board.add_visual_effect(VisualEffectType.FIRE, enemy.x, enemy.y)


class ChainMastery(Skill):
    """Chain Lightning hits 2 additional targets"""
    def __init__(self):
        super().__init__("Chain Mastery", "Chain Lightning hits 2 additional targets")
        self.is_passive = True
        self.skill_enum = PassiveSkill.CHAIN_MASTERY
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class ArcanePower(Skill):
    """Gain +25 intelligence"""
    def __init__(self):
        super().__init__("Arcane Power", "+25 intelligence")
        self.is_passive = True
        self.skill_enum = PassiveSkill.ARCANE_POWER
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

    def apply_to_owner(self, owner):
        owner.intelligence += 25


def create_wizard_skill(skill_name) -> Skill:
    skill_classes = {
        "chain_lightning": ChainLightning,
        PassiveSkill.FIRE_SPLASH: FireSplash,
        PassiveSkill.CHAIN_MASTERY: ChainMastery,
        PassiveSkill.ARCANE_POWER: ArcanePower,
    }

    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)

    if skill_class:
        return skill_class()
    return None
