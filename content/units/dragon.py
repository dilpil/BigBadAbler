import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from projectile import Projectile
from cloud_effect import CloudEffect
from visual_effect import VisualEffectType
import math


class FireBreath(Skill):
    """Breathes fire in a cone, dealing damage over time"""
    
    def __init__(self):
        super().__init__(
            name="Fire Breath",
            description="Breathe fire in a cone for 2 seconds, dealing 100 damage/s"
        )
        self.is_passive = False
        self.cast_time = 0.5
        self.mana_cost = 60
        self.breathing = False
        self.breath_timer = 0
        self.damage_timer = 0
        
    def should_cast(self, caster) -> bool:
        """Override to determine when to cast"""
        # Need a target in range and enough mana
        if self.current_mana < self.mana_cost:
            return False
        if caster.board:
            enemies = caster.board.get_enemy_units(caster.team)
            for enemy in enemies:
                if caster.board.get_distance(caster, enemy) <= 3:
                    return True
        return False
        
    def execute(self, caster):
        """Start breathing fire when cast completes"""
        self.breathing = True
        self.breath_timer = 2.0  # Breathe for 2 seconds
        self.damage_timer = 0
        self.current_mana = 0  # Consume mana
        
        # Visual effect
        if caster.board:
            caster.board.add_visual_effect(VisualEffectType.SPELL_CAST, caster.x, caster.y)
            
    def update(self, dt: float):
        super().update(dt)
        unit = self.owner  # Get unit from owner property
        
        if self.breathing:
            self.breath_timer -= dt
            self.damage_timer += dt
            
            # Deal damage every 0.2 seconds
            if self.damage_timer >= 0.2:
                self.damage_timer -= 0.2
                self.deal_cone_damage(unit)
                
            if self.breath_timer <= 0:
                self.breathing = False
                
    def deal_cone_damage(self, unit):
        """Deal damage to all enemies in a cone"""
        if not unit.board:
            return
            
        # Find direction to nearest enemy
        nearest = unit.board.get_nearest_enemy(unit)
        if not nearest:
            return
            
        # Calculate cone direction
        dx = nearest.x - unit.x
        dy = nearest.y - unit.y
        
        # Check all enemies
        enemies = unit.board.get_enemy_units(unit.team)
        for enemy in enemies:
            if not enemy.is_alive():
                continue
                
            # Check if enemy is in cone (simplified - just check distance and rough angle)
            distance = unit.board.get_distance(unit, enemy)
            if distance <= 3:  # 3 tile range
                # Deal damage
                damage = 20  # 20 damage per tick = 100 damage/s
                damage = int(damage * (1 + unit.intelligence / 100))
                enemy.take_damage(damage, "magical", unit)
                
                # Visual effect
                unit.board.add_visual_effect(VisualEffectType.DAMAGE_MAGIC, enemy.x, enemy.y)


class DragonPassive(Skill):
    """Dragon is immune to burn and has natural armor"""
    
    def __init__(self):
        super().__init__(
            name="Dragon Scales",
            description="Immune to burn, +50 armor and magic resist"
        )
        self.is_passive = True
        self.applied = False
        
    def update(self, dt: float):
        if not self.applied and self.owner:
            self.applied = True
            self.owner.armor += 50
            self.owner.magic_resist += 50
            
    def on_event(self, event_type, **kwargs):
        # Immune to burn effects
        if event_type == "status_applied" and kwargs.get("target") == self.owner:
            status = kwargs.get("status")
            if status and "burn" in status.name.lower():
                # Remove burn immediately
                self.owner.status_effects.remove(status)


class Dragon(Unit):
    def __init__(self):
        super().__init__(name="Dragon", unit_type=UnitType.NECROMANCER)  # Use existing type for now
        
        # Set dragon stats
        self.max_hp = 3000
        self.hp = self.max_hp
        self.max_mp = 150
        self.mp = self.max_mp
        self.attack_damage = 80
        self.attack_range = 2
        self.attack_speed = 0  # Base 1 attack/s
        self.armor = 50
        self.magic_resist = 50
        self.hp_regen = 10
        self.mp_regen = 3
        
        self.unit_type = UnitType.NECROMANCER  # Use existing type
        self.cost = 0  # Cannot be purchased normally
        
        # Visual properties
        self.color = (200, 50, 50)  # Red color
        self.letter = 'D'
        self.letter_color = (255, 200, 0)  # Gold letter
        
        # Add abilities
        self.starting_ability = FireBreath()
        self.abilities = [self.starting_ability, DragonPassive()]
        
        # Dragon is naturally large and intimidating
        self.strength = 50  # Bonus physical damage
        self.intelligence = 50  # Bonus magical damage