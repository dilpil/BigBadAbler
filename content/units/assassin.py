import sys
import os
import random
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
from skill import Skill
from status_effect import StatusEffect, StatModifierEffect, PoisonEffect

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
        
        # Track crit counter for Crit passive
        self.attack_count = 0
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_assassin_skill("teleport_strike")
        if default_skill:
            self.set_spell(default_skill)
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return [
            PassiveSkill.EVASION,
            PassiveSkill.KNIFE_TOSS,
            PassiveSkill.TURBO,
            PassiveSkill.POISON,
            PassiveSkill.AETHER_SWAP,
            PassiveSkill.SOUL_REAPING,
            PassiveSkill.CRIT
        ]
    
    def get_passive_skill_cost(self, skill_name) -> int:
        """Get the cost of a passive skill"""
        costs = {
            PassiveSkill.EVASION: 40,
            PassiveSkill.KNIFE_TOSS: 35,
            PassiveSkill.TURBO: 45,
            PassiveSkill.POISON: 30,
            PassiveSkill.AETHER_SWAP: 50,
            PassiveSkill.SOUL_REAPING: 35,
            PassiveSkill.CRIT: 40,
        }
        return costs.get(skill_name, 30)
    
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


class TurboEffect(StatModifierEffect):
    """Double attack speed for 4 seconds after teleport"""
    def __init__(self):
        super().__init__("Turbo", 4.0, {"attack_speed": 100})  # +100% attack speed


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
        
        # Aether Swap passive - swap places instead of teleporting next to
        if self._caster_has_passive_skill(caster, PassiveSkill.AETHER_SWAP):
            # Swap positions
            old_caster_x, old_caster_y = caster.x, caster.y
            old_target_x, old_target_y = target.x, target.y
            
            caster.board.move_unit(caster, old_target_x, old_target_y)
            caster.board.move_unit(target, old_caster_x, old_caster_y)
            
            # Deal magic damage instead of physical
            damage = caster.attack_damage * 2
            target.take_damage(damage, "magical", caster)
        else:
            # Normal teleport - find adjacent position to target
            adjacent_pos = self._find_adjacent_position(caster.board, target.x, target.y)
            if adjacent_pos:
                caster.board.move_unit(caster, adjacent_pos[0], adjacent_pos[1])
                
                # Calculate damage with crit check
                base_damage = caster.attack_damage * 2
                
                # Crit passive - every 4th attack deals 3x damage
                if self._caster_has_passive_skill(caster, PassiveSkill.CRIT):
                    caster.attack_count += 1
                    if caster.attack_count >= 4:
                        caster.attack_count = 0
                        base_damage = caster.attack_damage * 3  # 3x instead of 2x
                
                # Deal physical damage
                target.take_damage(base_damage, "physical", caster)
                
                # Apply poison if passive is active
                if self._caster_has_passive_skill(caster, PassiveSkill.POISON):
                    poison = PoisonEffect(10.0, 15.0)  # 10 second poison, 15 damage per tick
                    poison.source = caster
                    target.add_status_effect(poison)
        
        # Turbo passive - double attack speed for 4 seconds
        if self._caster_has_passive_skill(caster, PassiveSkill.TURBO):
            turbo = TurboEffect()
            turbo.source = caster
            caster.add_status_effect(turbo)
        
        # Knife Toss passive - damage another random enemy
        if self._caster_has_passive_skill(caster, PassiveSkill.KNIFE_TOSS):
            self._knife_toss(caster, target)
        
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
    
    def _knife_toss(self, caster, primary_target):
        """Knife Toss passive - damage another random enemy within 3 tiles"""
        enemies = caster.board.get_enemy_units(caster.team)
        potential_targets = []
        
        for enemy in enemies:
            if (enemy.is_alive() and enemy != primary_target and
                caster.board.distance(caster.x, caster.y, enemy.x, enemy.y) <= 3):
                potential_targets.append(enemy)
        
        if potential_targets:
            knife_target = random.choice(potential_targets)
            knife_damage = caster.attack_damage * 0.75  # 75% of normal attack damage
            knife_target.take_damage(knife_damage, "physical", caster)
            
            if caster.board:
                from visual_effect import VisualEffectType
                caster.board.add_visual_effect(VisualEffectType.PROJECTILE, knife_target.x, knife_target.y)
    
    def _caster_has_passive_skill(self, caster, skill_enum: PassiveSkill) -> bool:
        """Check if caster has a specific passive skill"""
        for passive in caster.passive_skills:
            if hasattr(passive, 'skill_enum') and passive.skill_enum == skill_enum:
                return True
        return False


class Evasion(Skill):
    """Gain 1 dodge every 2 seconds"""
    def __init__(self):
        super().__init__("Evasion", "Gain 1 dodge every 2 seconds (dodge blocks one attack)")
        self.is_passive = True
        self.skill_enum = PassiveSkill.EVASION
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.dodge_timer = 0
        self.dodge_interval = 2.0
        
    def update(self, dt: float):
        super().update(dt)
        if not self.owner or not self.owner.is_alive():
            return
            
        self.dodge_timer += dt
        if self.dodge_timer >= self.dodge_interval:
            self.dodge_timer -= self.dodge_interval
            
            # Check if unit already has dodge effect
            existing_dodge = None
            for effect in self.owner.status_effects:
                if effect.name == "Dodge":
                    existing_dodge = effect
                    break
            
            if existing_dodge:
                existing_dodge.stacks += 1
            else:
                dodge = DodgeEffect(1)
                dodge.source = self.owner
                self.owner.add_status_effect(dodge)


class KnifeToss(Skill):
    """On attack, also deal damage to another random enemy up to 3 tiles away"""
    def __init__(self):
        super().__init__("Knife Toss", "On attack, also deal damage to another random enemy up to 3 tiles away")
        self.is_passive = True
        self.skill_enum = PassiveSkill.KNIFE_TOSS
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class Turbo(Skill):
    """Double attack speed after teleport for 4 seconds"""
    def __init__(self):
        super().__init__("Turbo", "Double attack speed after teleport for 4 seconds")
        self.is_passive = True
        self.skill_enum = PassiveSkill.TURBO
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class Poison(Skill):
    """Attacks apply 1 stack of poison"""
    def __init__(self):
        super().__init__("Poison", "Attacks apply 1 stack of poison")
        self.is_passive = True
        self.skill_enum = PassiveSkill.POISON
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class AetherSwap(Skill):
    """Teleport swaps places with the target instead of teleporting next to it"""
    def __init__(self):
        super().__init__("Aether Swap", "Teleport swaps places with the target and deals magic instead of physical damage")
        self.is_passive = True
        self.skill_enum = PassiveSkill.AETHER_SWAP
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class SoulReaping(Skill):
    """When an adjacent enemy dies, heal for 400 HP"""
    def __init__(self):
        super().__init__("Soul Reaping", "When an adjacent enemy dies, heal for 400 HP")
        self.is_passive = True
        self.skill_enum = PassiveSkill.SOUL_REAPING
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_died" and "unit" in kwargs and "killer" in kwargs:
            dead_unit = kwargs["unit"]
            
            # Check if the dead unit was an enemy and adjacent to our owner
            if (self.owner and dead_unit.team != self.owner.team and
                self.owner.board.distance(self.owner.x, self.owner.y, dead_unit.x, dead_unit.y) <= 1):
                
                self.owner.heal(400, self.owner)
                
                if self.owner.board:
                    from visual_effect import VisualEffectType
                    self.owner.board.add_visual_effect(VisualEffectType.SOUL, self.owner.x, self.owner.y)


class Crit(Skill):
    """Every 4th attack deals 3x damage"""
    def __init__(self):
        super().__init__("Crit", "Every 4th attack deals 3x damage")
        self.is_passive = True
        self.skill_enum = PassiveSkill.CRIT
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


def create_assassin_skill(skill_name) -> Skill:
    """Create assassin-specific skills"""
    skill_classes = {
        "teleport_strike": TeleportStrike,
        PassiveSkill.EVASION: Evasion,
        PassiveSkill.KNIFE_TOSS: KnifeToss,
        PassiveSkill.TURBO: Turbo,
        PassiveSkill.POISON: Poison,
        PassiveSkill.AETHER_SWAP: AetherSwap,
        PassiveSkill.SOUL_REAPING: SoulReaping,
        PassiveSkill.CRIT: Crit,
    }
    
    # Handle both string and enum inputs for backwards compatibility
    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)
        
    if skill_class:
        return skill_class()
    return None