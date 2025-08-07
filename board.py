import math
from typing import List, Optional, Tuple, Set
from collections import deque
from visual_effect import VisualEffect, VisualEffectType
from text_floater import TextFloaterManager

class Board:
    def __init__(self, width: int = 10, height: int = 10):
        self.width = width
        self.height = height
        self.units = {}
        self.player_units = []
        self.enemy_units = []
        self.projectiles = []
        self.visual_effects = []
        self.text_floater_manager = TextFloaterManager()
        self.event_handlers = {}
        self.game = None  # Will be set by Game class
        self.corpses = []  # List of corpse positions for necromancer abilities
        
    def add_unit(self, unit, x: int, y: int, team: str):
        if self.is_valid_position(x, y) and not self.get_unit_at(x, y):
            unit.x = x
            unit.y = y
            unit.team = team
            self.units[(x, y)] = unit
            
            if team == "player":
                self.player_units.append(unit)
            else:
                self.enemy_units.append(unit)
            
            self.raise_event("unit_added", unit=unit)
            return True
        return False
    
    def remove_unit(self, unit):
        if (unit.x, unit.y) in self.units:
            del self.units[(unit.x, unit.y)]
            
        if unit in self.player_units:
            self.player_units.remove(unit)
        elif unit in self.enemy_units:
            self.enemy_units.remove(unit)
            
        self.raise_event("unit_removed", unit=unit)
    
    def clear(self):
        """Clear all units, projectiles, and visual effects from the board."""
        self.units.clear()
        self.player_units.clear()
        self.enemy_units.clear()
        self.projectiles.clear()
        self.visual_effects.clear()
        self.text_floater_manager.clear()
        self.corpses.clear()
    
    def move_unit(self, unit, new_x: int, new_y: int):
        if not self.is_valid_position(new_x, new_y):
            return False
            
        if self.get_unit_at(new_x, new_y):
            return False
            
        del self.units[(unit.x, unit.y)]
        unit.x = new_x
        unit.y = new_y
        self.units[(new_x, new_y)] = unit
        return True
    
    def get_unit_at(self, x: int, y: int):
        return self.units.get((x, y))
    
    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_distance(self, unit1, unit2) -> int:
        return max(abs(unit1.x - unit2.x), abs(unit1.y - unit2.y))
    
    def get_nearest_enemy(self, unit):
        enemies = self.enemy_units if unit.team == "player" else self.player_units
        if not enemies:
            return None
            
        nearest = None
        min_distance = float('inf')
        
        for enemy in enemies:
            if enemy.is_alive():
                distance = self.get_distance(unit, enemy)
                if distance < min_distance:
                    min_distance = distance
                    nearest = enemy
                    
        return nearest
    
    def get_units_in_range(self, x: int, y: int, range: int, team: Optional[str] = None) -> List:
        units_in_range = []
        
        for unit in self.get_all_units():
            if not unit.is_alive():
                continue
                
            if team and unit.team != team:
                continue
                
            distance = max(abs(unit.x - x), abs(unit.y - y))
            if distance <= range:
                units_in_range.append(unit)
                
        return units_in_range
    
    def get_all_units(self) -> List:
        return self.player_units + self.enemy_units
    
    def find_path(self, start_x: int, start_y: int, end_x: int, end_y: int) -> List[Tuple[int, int]]:
        if not self.is_valid_position(start_x, start_y) or not self.is_valid_position(end_x, end_y):
            return []
            
        start = (start_x, start_y)
        end = (end_x, end_y)
        
        if start == end:
            return [start]
            
        queue = deque([(start, [start])])
        visited = {start}
        
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        while queue:
            (x, y), path = queue.popleft()
            
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                new_pos = (new_x, new_y)
                
                if new_pos == end:
                    return path + [new_pos]
                    
                if (self.is_valid_position(new_x, new_y) and 
                    new_pos not in visited and 
                    not self.get_unit_at(new_x, new_y)):
                    visited.add(new_pos)
                    queue.append((new_pos, path + [new_pos]))
                    
        return []
    
    def raise_event(self, event_type: str, **kwargs):
        for unit in self.get_all_units():
            if not unit.is_alive():
                continue
                
            for skill in unit.iter_skills():
                if hasattr(skill, 'on_event'):
                    skill.on_event(event_type, **kwargs)
                    
            for item in unit.items:
                if hasattr(item, 'on_event'):
                    item.on_event(event_type, **kwargs)
                    
            for status in unit.status_effects[:]:
                if hasattr(status, 'on_event'):
                    status.on_event(event_type, **kwargs)
    
    def add_projectile(self, projectile):
        self.projectiles.append(projectile)
    
    def remove_projectile(self, projectile):
        if projectile in self.projectiles:
            self.projectiles.remove(projectile)
    
    def update_projectiles(self, dt: float):
        for projectile in self.projectiles[:]:
            projectile.update(dt)
            if projectile.reached_target:
                self.remove_projectile(projectile)
    
    def add_visual_effect(self, effect_type: VisualEffectType, x: int, y: int):
        """Add a visual effect at the specified position."""
        if self.is_valid_position(x, y):
            effect = VisualEffect(effect_type, x, y)
            self.visual_effects.append(effect)
    
    def make_text_floater(self, text: str, color: tuple, x: int = None, y: int = None, unit=None):      
        """Add a text floater at the specified position or unit's position."""
        if unit is not None:
            # Use unit's position if unit is provided
            pos_x, pos_y = unit.x, unit.y
        elif x is not None and y is not None:
            # Use provided coordinates
            pos_x, pos_y = x, y
        else:
            # Invalid parameters
            return
            
        if self.is_valid_position(pos_x, pos_y):
            self.text_floater_manager.add_text_floater(pos_x, pos_y, text, color)
    
    def update_visual_effects(self, dt: float):
        """Update visual effects and remove expired ones."""
        for effect in self.visual_effects[:]:
            effect.update(dt)
            if effect.is_expired():
                self.visual_effects.remove(effect)
    
    def update_combat(self, dt: float):
        """Update all combat entities - units, projectiles, and visual effects"""
        # Update projectiles
        self.update_projectiles(dt)
        
        # Update visual effects
        self.update_visual_effects(dt)
        
        # Update text floaters
        self.text_floater_manager.update(dt)
        
        # Update all units
        for unit in self.get_all_units():
            unit.update(dt)
            
    def add_corpse(self, x: int, y: int, dead_unit):
        """Add a corpse at the specified position"""
        corpse = {
            'x': x,
            'y': y,
            'unit_type': dead_unit.unit_type if hasattr(dead_unit, 'unit_type') else 'unknown',
            'team': dead_unit.team,
            'max_hp': dead_unit.max_hp,
            'name': dead_unit.name
        }
        self.corpses.append(corpse)
        
    def get_corpses_in_area(self, center_x: int, center_y: int, radius: int):
        """Get all corpses within radius of center position"""
        corpses_in_area = []
        for corpse in self.corpses:
            distance = self.get_distance_coords(center_x, center_y, corpse['x'], corpse['y'])
            if distance <= radius:
                corpses_in_area.append(corpse)
        return corpses_in_area
        
    def remove_corpse(self, corpse):
        """Remove a corpse from the board"""
        if corpse in self.corpses:
            self.corpses.remove(corpse)
            
    def get_distance_coords(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Get Chebyshev distance between two coordinates"""
        return max(abs(x2 - x1), abs(y2 - y1))