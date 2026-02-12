import sys
import os
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import StatusEffect

class Assassin(Unit):
    def __init__(self):
        super().__init__("Assassin", UnitType.ASSASSIN)
        self.max_hp = 450
        self.hp = self.max_hp
        self.max_mp = 150
        self.mp = 0
        self.attack_damage = 80
        self.attack_range = 1  # Melee unit
        self.attack_speed = 20  # 1.2 attacks per second
        self.strength = 20
        self.armor = 15
        self.magic_resist = 10
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_assassin_skill("teleport_strike")
        if default_skill:
            self.set_spell(default_skill)
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 55

def create_assassin() -> Assassin:
    """Factory function to create an assassin"""
    return Assassin()


# ===== ASSASSIN STATUS EFFECTS =====

class DodgeEffect(StatusEffect):
    """Dodge status effect that blocks one incoming attack"""
    def __init__(self, stacks: int = 1):
        super().__init__("Dodge", None)  # No duration - consumed on use
        self.stacks = stacks
        
    def on_event(self, event_type: str, **kwargs):
        if (event_type == "unit_attacked" and "target" in kwargs and 
            kwargs["target"] == self.unit and self.stacks > 0):
            
            # Consume one dodge stack
            self.stacks -= 1
            
            # Prevent damage by setting it to 0
            if "damage" in kwargs:
                kwargs["damage"] = 0
            
            # Add visual effect
            if self.unit.board:
                from visual_effect import VisualEffectType
                self.unit.board.add_visual_effect(VisualEffectType.DODGE, self.unit.x, self.unit.y)
            
            # Remove effect if no stacks remain
            if self.stacks <= 0:
                self.unit.remove_status_effect(self)


# ===== ASSASSIN SKILLS =====

class TeleportStrike(Skill):
    def __init__(self):
        super().__init__("Teleport Strike", "Teleport next to lowest hp enemy unit and attack it once for 2x damage")
        self.cast_time = 0.5
        self.mana_cost = 100
        
    def should_cast(self, caster) -> bool:
        # Cast if there are living enemies and we have mana
        if not caster.board:
            return False
        enemies = caster.board.get_enemy_units(caster.team)
        living_enemies = [enemy for enemy in enemies if enemy.is_alive()]
        return len(living_enemies) > 0
        
    def execute(self, caster):
        if not caster.board:
            return

        # Find lowest HP enemy (by percentage)
        enemies = caster.board.get_enemy_units(caster.team)
        living_enemies = [enemy for enemy in enemies if enemy.is_alive()]

        if not living_enemies:
            return

        target = min(living_enemies, key=lambda e: e.hp / e.max_hp)

        # Teleport to adjacent position to target
        adjacent_pos = self._find_adjacent_position(caster.board, target.x, target.y)
        if adjacent_pos:
            caster.board.move_unit(caster, adjacent_pos[0], adjacent_pos[1])

            # Deal 2x physical damage
            damage = caster.attack_damage * 2
            target.take_damage(damage, "physical", caster)

        # Visual effect
        if caster.board:
            from visual_effect import VisualEffectType
            caster.board.add_visual_effect(VisualEffectType.TELEPORT, caster.x, caster.y)
    
    def _find_adjacent_position(self, board, target_x, target_y):
        """Find an empty adjacent position to the target"""
        adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        random.shuffle(adjacent_offsets)  # Randomize order
        
        for dx, dy in adjacent_offsets:
            new_x, new_y = target_x + dx, target_y + dy
            if (board.is_valid_position(new_x, new_y) and 
                not board.get_unit_at(new_x, new_y)):
                return (new_x, new_y)
        
        # If no adjacent position available, find nearest empty position
        for distance in range(2, 8):
            for x in range(max(0, target_x - distance), min(8, target_x + distance + 1)):
                for y in range(max(0, target_y - distance), min(8, target_y + distance + 1)):
                    if (board.is_valid_position(x, y) and 
                        not board.get_unit_at(x, y)):
                        return (x, y)
        
        return None


def create_assassin_skill(skill_name) -> Skill:
    """Create assassin-specific skills"""
    skill_classes = {
        "teleport_strike": TeleportStrike,
    }

    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)

    if skill_class:
        return skill_class()
    return None