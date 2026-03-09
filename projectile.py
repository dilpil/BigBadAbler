import math
from typing import Optional, Callable, Union
from visual_effect import VisualEffectType

class Projectile:
    def __init__(self, source, target, speed: float = 10.0):
        """
        Create a projectile.
        
        Args:
            source: The unit that created this projectile
            target: Either a unit (for targeted projectiles) or None (for location-targeted)
            speed: Movement speed of the projectile
        """
        self.source = source
        self.target = target
        self.speed = speed
        
        self.x = float(source.x)
        self.y = float(source.y)
        self.start_x = float(source.x)
        self.start_y = float(source.y)
        
        # Target location for location-targeted projectiles
        self.target_x = None
        self.target_y = None
        
        self.reached_target = False
        self.on_hit_callback = None
        
        # Piercing behavior
        self.piercing = False
        self.hit_units = set()
        
        # Damage properties
        self.damage = 0
        self.damage_type = "physical"  # Legacy single type
        self.damage_types = None       # New multi-type system (list of DamageType)
        self.effects = []
        
        # Homing properties
        self.is_homing = False
        self.turn_rate = 5.0
        
    def set_target_location(self, x: float, y: float):
        """Set a target location for location-targeted projectiles"""
        self.target_x = x
        self.target_y = y
        self.target = None  # Clear unit target when using location targeting
        
    def set_on_hit(self, callback: Callable):
        self.on_hit_callback = callback
        
    def update(self, dt: float):
        if self.reached_target:
            return
            
        # Handle homing behavior
        if self.is_homing and self.target:
            if not self.target.is_alive():
                # Find new target for homing projectile
                if self.source and self.source.board:
                    nearest = self.source.board.get_nearest_enemy(self.source)
                    if nearest and nearest != self.target:
                        self.target = nearest
                    else:
                        self.reached_target = True
                        return
                else:
                    self.reached_target = True
                    return
        
        # Determine destination based on projectile type
        if self.target_x is not None and self.target_y is not None:
            # Location-targeted projectile
            dest_x = self.target_x
            dest_y = self.target_y
        elif self.target and self.target.is_alive():
            # Unit-targeted projectile
            dest_x = float(self.target.x)
            dest_y = float(self.target.y)
        else:
            # No valid target
            self.reached_target = True
            return
            
        dx = dest_x - self.x
        dy = dest_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 0.3:
            if self.target:
                # Unit-targeted projectile
                self.on_land(self.target)
                if not self.piercing:
                    self.reached_target = True
            else:
                # Location-targeted projectile - pass location to callback
                self.on_land_at_location(dest_x, dest_y)
                self.reached_target = True
            return
            
        move_distance = self.speed * dt
        if move_distance >= distance:
            self.x = dest_x
            self.y = dest_y
        else:
            self.x += (dx / distance) * move_distance
            self.y += (dy / distance) * move_distance
            
    def on_land(self, target):
        """Called when projectile hits a target unit"""
        if target in self.hit_units:
            return
            
        self.hit_units.add(target)
        
        if self.on_hit_callback:
            self.on_hit_callback(target)
        else:
            if self.damage > 0:
                dmg_types = self.damage_types if self.damage_types is not None else self.damage_type
                target.take_damage(self.damage, dmg_types, self.source)
                
            for effect in self.effects:
                target.add_status_effect(effect)
                
        if self.source and self.source.board:
            self.source.board.raise_event("projectile_hit", 
                                        projectile=self, 
                                        source=self.source, 
                                        target=target)
    
    def on_land_at_location(self, x: float, y: float):
        """Called when a location-targeted projectile reaches its destination"""
        if self.on_hit_callback:
            # Pass projectile, x, y to callback for location-based effects
            self.on_hit_callback(self, x, y)
        # No default behavior for location-targeted projectiles without callbacks

