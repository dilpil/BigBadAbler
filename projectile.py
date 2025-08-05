import math
from typing import Optional, Callable
from visual_effect import VisualEffectType

class Projectile:
    def __init__(self, source, target, speed: float = 10.0):
        self.source = source
        self.target = target
        self.speed = speed
        
        self.x = float(source.x)
        self.y = float(source.y)
        self.start_x = float(source.x)
        self.start_y = float(source.y)
        
        self.reached_target = False
        self.on_hit_callback = None
        self.piercing = False
        self.hit_units = set()
        
        self.damage = 0
        self.damage_type = "physical"
        self.effects = []
        
    def set_on_hit(self, callback: Callable):
        self.on_hit_callback = callback
        
    def update(self, dt: float):
        if self.reached_target:
            return
            
        if not self.target or not self.target.is_alive():
            self.reached_target = True
            return
            
        target_x = float(self.target.x)
        target_y = float(self.target.y)
        
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 0.3:
            self.on_land(self.target)
            if not self.piercing:
                self.reached_target = True
            return
            
        move_distance = self.speed * dt
        if move_distance >= distance:
            self.x = target_x
            self.y = target_y
        else:
            self.x += (dx / distance) * move_distance
            self.y += (dy / distance) * move_distance
            
    def on_land(self, target):
        if target in self.hit_units:
            return
            
        self.hit_units.add(target)
        
        if self.on_hit_callback:
            self.on_hit_callback(target)
        else:
            if self.damage > 0:
                target.take_damage(self.damage, self.damage_type, self.source)
                
            for effect in self.effects:
                target.add_status_effect(effect)
                
        if self.source and self.source.board:
            self.source.board.raise_event("projectile_hit", 
                                        projectile=self, 
                                        source=self.source, 
                                        target=target)


class HomingProjectile(Projectile):
    def __init__(self, source, target, speed: float = 10.0):
        super().__init__(source, target, speed)
        self.turn_rate = 5.0
        
    def update(self, dt: float):
        if self.reached_target:
            return
            
        if not self.target or not self.target.is_alive():
            nearest = self.source.board.get_nearest_enemy(self.source)
            if nearest and nearest != self.target:
                self.target = nearest
            else:
                self.reached_target = True
                return
                
        super().update(dt)


class AoEProjectile(Projectile):
    def __init__(self, source, target_x: float, target_y: float, speed: float = 10.0):
        super().__init__(source, None, speed)
        self.target_x = target_x
        self.target_y = target_y
        self.explosion_radius = 2
        self.exploded = False
        
    def update(self, dt: float):
        if self.reached_target:
            return
            
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 0.3:
            self.explode()
            self.reached_target = True
            return
            
        move_distance = self.speed * dt
        if move_distance >= distance:
            self.x = self.target_x
            self.y = self.target_y
        else:
            self.x += (dx / distance) * move_distance
            self.y += (dy / distance) * move_distance
            
    def explode(self):
        if self.exploded:
            return
            
        self.exploded = True
        
        units = self.source.board.get_units_in_range(int(self.x), int(self.y), self.explosion_radius)
        
        for unit in units:
            if unit.team != self.source.team:
                self.on_land(unit)
        
        # Add fire visual effects to all tiles in explosion radius
        center_x, center_y = int(self.x), int(self.y)
        for dx in range(-self.explosion_radius, self.explosion_radius + 1):
            for dy in range(-self.explosion_radius, self.explosion_radius + 1):
                tile_x, tile_y = center_x + dx, center_y + dy
                # Check if tile is within circular explosion radius
                distance = math.sqrt(dx * dx + dy * dy)
                if distance <= self.explosion_radius and self.source.board.is_valid_position(tile_x, tile_y):
                    self.source.board.add_visual_effect(VisualEffectType.FIRE, tile_x, tile_y)
                
        if self.source and self.source.board:
            self.source.board.raise_event("aoe_explosion", 
                                        projectile=self, 
                                        source=self.source, 
                                        x=self.x, 
                                        y=self.y)