import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from projectile import Projectile
from status_effect import StatusEffect, StatModifierEffect
import math

class Pyromancer(Unit):
    def __init__(self):
        super().__init__("Pyromancer", UnitType.PYROMANCER)
        self.max_hp = 550
        self.hp = self.max_hp
        self.max_mp = 80
        self.mp = 20
        self.attack_damage = 40
        self.attack_range = 4
        self.attack_speed = -15  # 0.85 attacks per second
        self.intelligence = 30
        self.armor = 20
        self.magic_resist = 20

        # Set default skill immediately upon creation
        self._set_default_skill()

    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_pyromancer_skill("fireball")
        if default_skill:
            self.set_spell(default_skill)

    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_pyromancer() -> Pyromancer:
    """Factory function to create a pyromancer"""
    return Pyromancer()


# ===== PYROMANCER SKILLS =====

class Fireball(Skill):
    def __init__(self):
        super().__init__("Fireball", "Launches an explosive fireball dealing 250 (+30% INT) fire damage in a radius 2 area")
        self.cast_time = 0.25
        self.mana_cost = 80
        self.range = 6
        self.aoe_radius = 2
        self.damage = 250

    def should_cast(self, caster) -> bool:
        return len(self.get_valid_targets(caster, "enemy")) > 0

    def execute(self, caster):
        targets = self.get_valid_targets(caster, "enemy")
        if targets:
            target = targets[0]  # Use first valid target
            radius = self.aoe_radius

            # Create a standard projectile with location targeting
            from projectile import Projectile
            projectile = Projectile(caster, None, speed=8.0)
            projectile.set_target_location(target.x, target.y)

            # Calculate damage
            damage = self.damage * (1 + caster.intelligence / 100)

            # Create explosion callback that handles fireball effects
            def fireball_explosion(proj, x, y):
                """Handle fireball explosion at location"""
                if not caster.board:
                    return

                # Get all units in explosion radius
                units_in_area = []
                for unit in caster.board.get_all_units():
                    distance = caster.board.get_distance_to_point(unit, x, y)
                    if distance <= radius:
                        units_in_area.append(unit)

                enemies_hit = [u for u in units_in_area if u.team != caster.team and u.is_alive()]

                # Deal damage to enemies
                for enemy in enemies_hit:
                    enemy.take_damage(damage, "fire", caster)

                # Add visual effects
                from visual_effect import VisualEffectType
                center_x, center_y = int(x), int(y)
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        tile_x, tile_y = center_x + dx, center_y + dy
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist <= radius and caster.board.is_valid_position(tile_x, tile_y):
                            caster.board.add_visual_effect(VisualEffectType.FIRE, tile_x, tile_y)

            projectile.on_hit_callback = fireball_explosion
            caster.board.add_projectile(projectile)


def create_pyromancer_skill(skill_name: str) -> Skill:
    """Create pyromancer-specific skills"""
    skill_classes = {
        "fireball": Fireball,
    }

    skill_class = skill_classes.get(skill_name)
    if skill_class:
        return skill_class()
    return None
