import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
from skill import Skill
from projectile import AoEProjectile, Projectile
from cloud_effect import FirestormCloud
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
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return [
            PassiveSkill.FIRESTORM,
            PassiveSkill.BIG_FIREBALL,
            PassiveSkill.SHRAPNEL,
            PassiveSkill.FLAME_BATH,
            PassiveSkill.FLAMESHOCK,
            PassiveSkill.FLAMEBOLTS,
            PassiveSkill.FLAMEPROOF_AURA
        ]
    
    def get_passive_skill_cost(self, skill_name) -> int:
        """Get the cost of a passive skill"""
        costs = {
            PassiveSkill.FIRESTORM: 40,
            PassiveSkill.BIG_FIREBALL: 30,
            PassiveSkill.SHRAPNEL: 45,
            PassiveSkill.FLAME_BATH: 35,
            PassiveSkill.FLAMESHOCK: 50,
            PassiveSkill.FLAMEBOLTS: 35,
            PassiveSkill.FLAMEPROOF_AURA: 40
        }
        return costs.get(skill_name, 35)
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_pyromancer() -> Pyromancer:
    """Factory function to create a pyromancer"""
    return Pyromancer()


# ===== CUSTOM STATUS EFFECTS =====

class StunEffect(StatusEffect):
    """Stun effect that prevents unit actions"""
    def __init__(self, duration: float = 1.5):
        super().__init__("Stunned", duration)
        
    def apply(self, unit):
        super().apply(unit)
        # Force unit to idle state and prevent actions
        unit.state = unit.__class__.__dict__.get('UnitState', type('UnitState', (), {'IDLE': 'idle'})).IDLE
        if hasattr(unit, 'target'):
            unit.target = None
        if hasattr(unit, 'cast_skill'):
            unit.cast_skill = None


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
        # Check for passive upgrades that modify mana cost
        firestorm = PassiveSkill.FIRESTORM in caster.passive_skills
        mana_cost_multiplier = 1.5 if firestorm else 1.0
        
        targets = self.get_valid_targets(caster, "enemy")
        if targets:
            target = targets[0]  # Use first valid target
            
            # Check for Big Fireball upgrade (increases radius)
            big_fireball = PassiveSkill.BIG_FIREBALL in caster.passive_skills
            radius = self.aoe_radius + 1 if big_fireball else self.aoe_radius
            
            projectile = EnhancedFireballProjectile(caster, target.x, target.y, speed=8.0)
            projectile.damage = self.damage * (1 + caster.intelligence / 100)
            projectile.explosion_radius = radius
            projectile.caster = caster
            caster.board.add_projectile(projectile)


class EnhancedFireballProjectile(AoEProjectile):
    """Enhanced fireball projectile that supports pyromancer passive abilities"""
    def __init__(self, source, target_x: float, target_y: float, speed: float = 10.0):
        super().__init__(source, target_x, target_y, speed)
        self.damage_type = "fire"
        self.caster = source
        
    def explode(self):
        """Override explode to implement enhanced fireball effects"""
        if self.exploded:
            return
            
        self.exploded = True
        
        if not self.caster or not self.caster.board:
            return
            
        # Get all units in explosion radius
        units_in_area = []
        for unit in self.caster.board.get_all_units():
            distance = self.caster.board.get_distance_to_point(unit, self.target_x, self.target_y)
            if distance <= self.explosion_radius:
                units_in_area.append(unit)
        
        enemies_hit = [u for u in units_in_area if u.team != self.caster.team and u.is_alive()]
        allies_in_area = [u for u in units_in_area if u.team == self.caster.team and u.is_alive()]
        
        # Deal damage to enemies
        total_damage_dealt = 0
        for enemy in enemies_hit:
            damage_dealt = enemy.take_damage(self.damage, self.damage_type, self.caster)
            total_damage_dealt += damage_dealt
            
        # Check for passive upgrades and apply effects
        self.apply_passive_effects(enemies_hit, allies_in_area, total_damage_dealt)
            
    def apply_passive_effects(self, enemies_hit, allies_in_area, total_damage_dealt):
        """Apply effects from pyromancer passive skills"""
        if not self.caster:
            return
            
        # Firestorm: Create damage zone
        if PassiveSkill.FIRESTORM in self.caster.passive_skills:
            firestorm_damage = self.damage * 0.5  # 50% of initial damage
            firestorm = FirestormCloud(self.target_x, self.target_y, self.explosion_radius, 
                                     firestorm_damage, self.caster)
            self.caster.board.add_cloud_effect(firestorm)
            
        # Shrapnel: Shoot projectiles at 4 nearest enemies
        if PassiveSkill.SHRAPNEL in self.caster.passive_skills:
            self.create_shrapnel_projectiles()
            
        # Flame Bath: Heal allies
        if PassiveSkill.FLAME_BATH in self.caster.passive_skills and total_damage_dealt > 0:
            heal_amount = total_damage_dealt * 0.5 / len(allies_in_area) if allies_in_area else 0
            for ally in allies_in_area:
                ally.heal(heal_amount, self.caster)
                
        # Flameshock: Stun enemies
        if PassiveSkill.FLAMESHOCK in self.caster.passive_skills:
            for enemy in enemies_hit:
                stun = StunEffect(1.5)
                stun.source = self.caster
                enemy.add_status_effect(stun)
    
    def create_shrapnel_projectiles(self):
        """Create shrapnel projectiles targeting nearest enemies"""
        if not self.caster.board:
            return
            
        # Find all enemies
        enemies = self.caster.board.get_enemy_units(self.caster.team)
        if not enemies:
            return
            
        # Sort by distance to explosion point
        enemies.sort(key=lambda e: self.caster.board.get_distance_to_point(e, self.target_x, self.target_y))
        
        # Create projectiles for up to 4 nearest enemies
        for enemy in enemies[:4]:
            if enemy.is_alive():
                shrapnel = Projectile(type('DummySource', (), {
                    'x': self.target_x, 'y': self.target_y, 'team': self.caster.team
                })(), enemy, speed=12)
                shrapnel_damage = self.damage * 0.3  # 30% of fireball damage as physical
                shrapnel.on_hit_callback = lambda target, dmg=shrapnel_damage: target.take_damage(dmg, "physical", self.caster)
                self.caster.board.add_projectile(shrapnel)


class Firestorm(Skill):
    """Passive: Fireball creates a damage zone for 2 seconds, +50% mana cost"""
    def __init__(self):
        super().__init__("Firestorm", "Fireball creates a firestorm zone dealing 50% damage per second for 2 seconds (+50% mana cost)")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FIRESTORM


class BigFireball(Skill):
    """Passive: Fireball radius increased by 1"""
    def __init__(self):
        super().__init__("Big Fireball", "Fireball explosion radius increased by 1")
        self.is_passive = True
        self.skill_enum = PassiveSkill.BIG_FIREBALL


class Shrapnel(Skill):
    """Passive: Fireball shoots projectiles at 4 nearest enemies"""
    def __init__(self):
        super().__init__("Shrapnel", "Fireball shoots shrapnel projectiles at the 4 nearest enemies dealing physical damage")
        self.is_passive = True
        self.skill_enum = PassiveSkill.SHRAPNEL


class FlameBath(Skill):
    """Passive: Fireball heals allies in radius for half damage dealt"""
    def __init__(self):
        super().__init__("Flame Bath", "Fireball heals allies in the area for half the damage dealt to enemies")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FLAME_BATH


class Flameshock(Skill):
    """Passive: Fireball stuns enemies for 1.5 seconds"""
    def __init__(self):
        super().__init__("Flameshock", "Fireball stuns all enemies hit for 1.5 seconds")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FLAMESHOCK


class Flamebolts(Skill):
    """Passive: Attacks deal additional fire damage based on INT"""
    def __init__(self):
        super().__init__("Flamebolts", "Attacks deal additional fire damage equal to Intelligence")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FLAMEBOLTS
        
    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_attack" and kwargs.get("attacker") == owner:
            target = kwargs.get("target")
            if target and target.is_alive() and owner:
                fire_damage = owner.intelligence
                target.take_damage(fire_damage, "fire", owner)


class FlameproofAura(Skill):
    """Passive: Allies gain 50 fire resistance at battle start"""
    def __init__(self):
        super().__init__("Flameproof Aura", "All allies gain +50 fire resistance at the start of battle")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FLAMEPROOF_AURA
        self.applied = False
        
    def on_event(self, event_type: str, **kwargs):
        # Apply fire resistance at first combat frame
        owner = getattr(self, 'owner', None)
        if not self.applied and owner and owner.board:
            self.apply_fire_resistance()
            
    def apply_fire_resistance(self):
        owner = getattr(self, 'owner', None)
        if self.applied or not owner or not owner.board:
            return
            
        self.applied = True
        allies = owner.board.get_allied_units(owner.team)
        for ally in allies:
            ally.fire_resist += 50


def create_pyromancer_skill(skill_name: str) -> Skill:
    """Create pyromancer-specific skills"""
    skill_classes = {
        "fireball": Fireball,
        PassiveSkill.FIRESTORM: Firestorm,
        PassiveSkill.BIG_FIREBALL: BigFireball,
        PassiveSkill.SHRAPNEL: Shrapnel,
        PassiveSkill.FLAME_BATH: FlameBath,
        PassiveSkill.FLAMESHOCK: Flameshock,
        PassiveSkill.FLAMEBOLTS: Flamebolts,
        PassiveSkill.FLAMEPROOF_AURA: FlameproofAura,
        # String versions for compatibility
        "firestorm": Firestorm,
        "big_fireball": BigFireball,
        "shrapnel": Shrapnel,
        "flame_bath": FlameBath,
        "flameshock": Flameshock,
        "flamebolts": Flamebolts,
        "flameproof_aura": FlameproofAura,
    }
    
    skill_class = skill_classes.get(skill_name)
    if skill_class:
        return skill_class()
    return None