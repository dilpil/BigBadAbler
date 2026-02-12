import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
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
        self.set_spell(ChainLightning())

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

        damage = self.damage * (1 + caster.intelligence / 100)

        enemies = caster.board.get_enemy_units(caster.team)
        enemies = [e for e in enemies if e.is_alive()]
        if not enemies:
            return

        # Start with nearest enemy
        import random
        hit_enemies = []
        current_target = min(enemies, key=lambda e: caster.board.get_distance(caster, e))

        for _ in range(self.chain_count):
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
