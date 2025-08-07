from typing import Dict, Optional
from constants import FRAME_TIME

class StatusEffect:
    def __init__(self, name: str, duration: float):
        self.name = name
        self.duration = duration
        self.remaining_duration = duration
        self.unit = None
        self.source = None
        
        self.tick_interval = 0.5
        self.tick_timer = 0
        
        self.stat_modifiers = {}
        
    def apply(self, unit):
        self.unit = unit
        
    def remove(self, unit):
        self.unit = None
        
    def update(self, dt: float):
        self.remaining_duration -= dt
        
        if self.tick_interval > 0:
            self.tick_timer += dt
            if self.tick_timer >= self.tick_interval:
                self.tick_timer -= self.tick_interval
                self.on_tick()
                
    def on_tick(self):
        pass
    
    def is_expired(self) -> bool:
        return self.remaining_duration <= 0
    
    def on_event(self, event_type: str, **kwargs):
        pass


class DamageOverTimeEffect(StatusEffect):
    def __init__(self, name: str, duration: float, damage_per_tick: float, damage_type: str = "magical"):
        super().__init__(name, duration)
        self.damage_per_tick = damage_per_tick
        self.damage_type = damage_type
        
    def on_tick(self):
        if self.unit and self.unit.is_alive():
            self.unit.take_damage(self.damage_per_tick, self.damage_type, self.source)


class HealOverTimeEffect(StatusEffect):
    def __init__(self, name: str, duration: float, heal_per_tick: float):
        super().__init__(name, duration)
        self.heal_per_tick = heal_per_tick
        
    def on_tick(self):
        if self.unit and self.unit.is_alive():
            self.unit.heal(self.heal_per_tick, self.source)


class StatModifierEffect(StatusEffect):
    def __init__(self, name: str, duration: float, stat_changes: Dict[str, float]):
        super().__init__(name, duration)
        self.stat_modifiers = stat_changes
        
    def apply(self, unit):
        super().apply(unit)
        for stat, value in self.stat_modifiers.items():
            if hasattr(unit, stat):
                setattr(unit, stat, getattr(unit, stat) + value)
                
    def remove(self, unit):
        for stat, value in self.stat_modifiers.items():
            if hasattr(unit, stat):
                setattr(unit, stat, getattr(unit, stat) - value)
        super().remove(unit)


class PoisonEffect(DamageOverTimeEffect):
    def __init__(self, duration: float = 5.0, damage: float = 5.0):
        super().__init__("Poison", duration, damage, "magical")
        self.tick_interval = 5 * FRAME_TIME


class WeaknessEffect(StatModifierEffect):
    def __init__(self, duration: float = 3.0, damage_reduction: float = 0.25):
        super().__init__("Weakness", duration, {"strength": -25, "intelligence": -25})
        self.damage_reduction = damage_reduction


class DumbfoundEffect(StatusEffect):
    def __init__(self, duration: float = 2.0):
        super().__init__("Dumbfound", duration)
        
    def apply(self, unit):
        super().apply(unit)
        for skill in unit.skills:
            if not skill.is_passive:
                skill.current_cooldown = max(skill.current_cooldown, self.duration)


class RegenerationEffect(HealOverTimeEffect):
    def __init__(self, duration: float = 5.0, heal: float = 3.0):
        super().__init__("Regeneration", duration, heal)
        self.tick_interval = 5 * FRAME_TIME


class ProtectionEffect(StatModifierEffect):
    def __init__(self, duration: float = 4.0):
        super().__init__("Protection", duration, {})
        
    def apply(self, unit):
        super().apply(unit)
        self.original_armor = unit.armor
        self.original_mr = unit.magic_resist
        unit.armor *= 2
        unit.magic_resist *= 2
        
    def remove(self, unit):
        unit.armor = self.original_armor
        unit.magic_resist = self.original_mr
        super().remove(unit)


class AbsorbShieldEffect(StatusEffect):
    """Absorbs incoming damage up to a certain amount"""
    def __init__(self, name: str, duration: float, absorb_amount: float):
        super().__init__(name, duration)
        self.absorb_amount = absorb_amount
        self.remaining_absorb = absorb_amount
        
    def on_damage_taken(self, unit, damage_amount: float, damage_type: str, source) -> float:
        """Intercept damage and absorb it"""
        if self.remaining_absorb <= 0:
            return damage_amount
            
        absorbed = min(damage_amount, self.remaining_absorb)
        self.remaining_absorb -= absorbed
        remaining_damage = damage_amount - absorbed
        
        if self.remaining_absorb <= 0:
            # Shield is broken
            self.expire()
            
        return remaining_damage


class PlagueEffect(DamageOverTimeEffect):
    """Disease that spreads to nearby enemies"""
    def __init__(self, name: str, duration: float, damage_per_tick: float, spread_radius: int = 2):
        super().__init__(name, duration, damage_per_tick)
        self.spread_radius = spread_radius
        self.spread_timer = 0.0
        self.spread_interval = 2.0  # Try to spread every 2 seconds
        
    def update(self, unit, dt: float):
        super().update(unit, dt)
        
        # Try to spread the plague
        self.spread_timer += dt
        if self.spread_timer >= self.spread_interval:
            self.spread_timer = 0.0
            self.try_spread(unit)
            
    def try_spread(self, unit):
        """Try to spread plague to nearby enemies"""
        if not unit.board:
            return
            
        # Find nearby enemies without plague
        nearby_enemies = unit.board.get_units_in_range(unit.x, unit.y, self.spread_radius, 
                                                      "enemy" if unit.team == "player" else "player")
        
        candidates = [enemy for enemy in nearby_enemies 
                     if enemy.is_alive() and not any(eff.name == "Plague" for eff in enemy.status_effects)]
        
        if candidates:
            import random
            target = random.choice(candidates)
            plague = PlagueEffect("Plague", self.duration * 0.7, self.damage_per_tick * 0.8)
            plague.source = self.source
            target.add_status_effect(plague)