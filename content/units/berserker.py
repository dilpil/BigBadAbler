import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
from skill import Skill
from status_effect import StatusEffect, StatModifierEffect
import math

class Berserker(Unit):
    def __init__(self):
        super().__init__("Berserker", UnitType.BERSERKER)
        self.max_hp = 750
        self.hp = self.max_hp
        self.max_mp = 70
        self.mp = 0
        self.attack_damage = 70
        self.attack_range = 1
        self.strength = 25
        self.attack_speed = 0  # 1.0 attacks per second
        self.armor = 35
        self.magic_resist = 35
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_berserker_skill("frenzy")
        if default_skill:
            self.set_spell(default_skill)
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return [
            PassiveSkill.FAST_FRENZY,
            PassiveSkill.HUNGRY_FRENZY,
            PassiveSkill.IMMORTAL_FRENZY,
            PassiveSkill.LEAP,
            PassiveSkill.FRENZY_CRY,
            PassiveSkill.RIPPER,
            PassiveSkill.CLEAVE
        ]
    
    def get_passive_skill_cost(self, skill_name) -> int:
        """Get the cost of a passive skill"""
        costs = {
            PassiveSkill.FAST_FRENZY: 30,
            PassiveSkill.HUNGRY_FRENZY: 35,
            PassiveSkill.IMMORTAL_FRENZY: 40,
            PassiveSkill.LEAP: 45,
            PassiveSkill.FRENZY_CRY: 50,
            PassiveSkill.RIPPER: 35,
            PassiveSkill.CLEAVE: 40
        }
        return costs.get(skill_name, 35)
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_berserker() -> Berserker:
    """Factory function to create a berserker"""
    return Berserker()


# ===== CUSTOM STATUS EFFECTS =====

class FrenzyEffect(StatusEffect):
    """Custom status effect for Frenzy that provides attack speed, lifesteal, and optionally armor"""
    def __init__(self, duration: float = -1):  # -1 means until end of combat
        super().__init__("Frenzy", duration)
        self.attack_speed_bonus = 10
        self.lifesteal_percent = 5
        self.armor_bonus = 0
        self.magic_resist_bonus = 0
        
    def apply(self, unit):
        super().apply(unit)
        # Apply stat bonuses
        unit.attack_speed += self.attack_speed_bonus
        unit.armor += self.armor_bonus
        unit.magic_resist += self.magic_resist_bonus
        
    def remove(self, unit):
        # Remove stat bonuses
        unit.attack_speed -= self.attack_speed_bonus
        unit.armor -= self.armor_bonus
        unit.magic_resist -= self.magic_resist_bonus
        super().remove(unit)
        
    def on_event(self, event_type: str, **kwargs):
        # Handle lifesteal on attack
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            damage_dealt = kwargs.get("damage", 0)
            if damage_dealt > 0:
                heal_amount = damage_dealt * (self.lifesteal_percent / 100.0)
                self.unit.heal(heal_amount, self.unit)


# ===== BERSERKER SKILLS =====

class Frenzy(Skill):
    def __init__(self):
        super().__init__("Frenzy", "Gain 10% attack speed and 5% lifesteal until end of combat")
        self.cast_time = 0.3
        self.mana_cost = 40
        self.range = 0
        
    def should_cast(self, caster) -> bool:
        return not any(e.name == "Frenzy" for e in caster.status_effects)
        
    def execute(self, caster):
        # Check for passive upgrades
        fast_frenzy = PassiveSkill.FAST_FRENZY in caster.passive_skills
        hungry_frenzy = PassiveSkill.HUNGRY_FRENZY in caster.passive_skills
        immortal_frenzy = PassiveSkill.IMMORTAL_FRENZY in caster.passive_skills
        frenzy_cry = PassiveSkill.FRENZY_CRY in caster.passive_skills
        
        # Create frenzy effect with upgrades
        effect = FrenzyEffect()
        
        if fast_frenzy:
            effect.attack_speed_bonus = 15  # Upgrade from 10 to 15
            
        if hungry_frenzy:
            effect.lifesteal_percent = 10  # Upgrade from 5 to 10
            
        if immortal_frenzy:
            effect.armor_bonus = 10
            effect.magic_resist_bonus = 10
            
        effect.source = caster
        caster.add_status_effect(effect)
        
        # Apply to allies if Frenzy Cry is active
        if frenzy_cry and caster.board:
            allies = caster.board.get_allied_units(caster.team)
            for ally in allies:
                if ally != caster:  # Don't apply twice to caster
                    ally_effect = FrenzyEffect()
                    ally_effect.attack_speed_bonus = effect.attack_speed_bonus
                    ally_effect.lifesteal_percent = effect.lifesteal_percent
                    ally_effect.armor_bonus = effect.armor_bonus
                    ally_effect.magic_resist_bonus = effect.magic_resist_bonus
                    ally_effect.source = caster
                    ally.add_status_effect(ally_effect)


class FastFrenzy(Skill):
    """Passive: Increases Frenzy attack speed bonus from 10% to 15%"""
    def __init__(self):
        super().__init__("Fast Frenzy", "Frenzy attack speed bonus increased from 10% to 15%")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FAST_FRENZY


class HungryFrenzy(Skill):
    """Passive: Increases Frenzy lifesteal from 5% to 10%"""
    def __init__(self):
        super().__init__("Hungry Frenzy", "Frenzy lifesteal increased from 5% to 10%")
        self.is_passive = True
        self.skill_enum = PassiveSkill.HUNGRY_FRENZY


class ImmortalFrenzy(Skill):
    """Passive: Frenzy also grants 10 armor and 10 magic resist"""
    def __init__(self):
        super().__init__("Immortal Frenzy", "Frenzy also grants 10 armor and 10 magic resist")
        self.is_passive = True
        self.skill_enum = PassiveSkill.IMMORTAL_FRENZY


class Leap(Skill):
    """Passive: On kill, leap to the lowest HP enemy within 3 tiles"""
    def __init__(self):
        super().__init__("Leap", "On kill, leap to the lowest HP enemy within 3 tiles and attack")
        self.is_passive = True
        self.skill_enum = PassiveSkill.LEAP
        
    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_death" and kwargs.get("killer") == owner:
            self.perform_leap()
    
    def perform_leap(self):
        owner = getattr(self, 'owner', None)
        if not owner or not owner.board:
            return
            
        # Find lowest HP enemy within 3 tiles
        enemies = owner.board.get_enemy_units(owner.team)
        valid_targets = []
        
        for enemy in enemies:
            distance = owner.board.get_distance(owner, enemy)
            if distance <= 3 and enemy.is_alive():
                valid_targets.append(enemy)
        
        if not valid_targets:
            return
            
        # Find lowest HP target
        target = min(valid_targets, key=lambda e: e.hp)
        
        # Leap to target (find adjacent position)
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        leap_pos = None
        
        for dx, dy in directions:
            x, y = target.x + dx, target.y + dy
            if owner.board.is_valid_position(x, y) and not owner.board.get_unit_at(x, y):
                leap_pos = (x, y)
                break
        
        if leap_pos:
            # Move berserker to leap position
            old_x, old_y = owner.x, owner.y
            owner.board.move_unit(owner, leap_pos[0], leap_pos[1])
            
            # Force attack the target
            if owner.board.get_distance(owner, target) <= owner.attack_range:
                owner.attack(target)


class FrenzyCry(Skill):
    """Passive: Frenzy effects all allies"""
    def __init__(self):
        super().__init__("Frenzy Cry", "Frenzy also affects all allied units")
        self.is_passive = True
        self.skill_enum = PassiveSkill.FRENZY_CRY


class Ripper(Skill):
    """Passive: On hit, reduce target's armor by 1 permanently"""
    def __init__(self):
        super().__init__("Ripper", "Attacks permanently reduce target's armor by 1")
        self.is_passive = True
        self.skill_enum = PassiveSkill.RIPPER
        
    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_attack" and kwargs.get("attacker") == owner:
            target = kwargs.get("target")
            if target and target.is_alive():
                target.armor = max(0, target.armor - 1)  # Don't go below 0


class Cleave(Skill):
    """Passive: Primary attacks also hit up to 3 adjacent enemies"""
    def __init__(self):
        super().__init__("Cleave", "Attacks also hit up to 3 adjacent enemies for full damage")
        self.is_passive = True
        self.skill_enum = PassiveSkill.CLEAVE
        
    def on_event(self, event_type: str, **kwargs):
        owner = getattr(self, 'owner', None)
        if event_type == "unit_attack" and kwargs.get("attacker") == owner:
            primary_target = kwargs.get("target")
            self.perform_cleave(primary_target)
    
    def perform_cleave(self, primary_target):
        owner = getattr(self, 'owner', None)
        if not owner or not owner.board or not primary_target:
            return
            
        # Find adjacent enemies to primary target
        enemies = owner.board.get_enemy_units(owner.team)
        cleave_targets = []
        
        for enemy in enemies:
            if enemy != primary_target and enemy.is_alive():
                # Check if enemy is adjacent to primary target
                distance = owner.board.get_distance(primary_target, enemy)
                if distance <= 1:
                    cleave_targets.append(enemy)
        
        # Hit up to 3 adjacent enemies
        for target in cleave_targets[:3]:
            damage = owner.attack_damage
            # Apply strength bonus
            if owner.strength > 0:
                damage *= (1 + owner.strength / 100.0)
            
            target.take_damage(damage, "physical", owner)


def create_berserker_skill(skill_name: str) -> Skill:
    """Create berserker-specific skills"""
    skill_classes = {
        "frenzy": Frenzy,
        PassiveSkill.FAST_FRENZY: FastFrenzy,
        PassiveSkill.HUNGRY_FRENZY: HungryFrenzy,
        PassiveSkill.IMMORTAL_FRENZY: ImmortalFrenzy,
        PassiveSkill.LEAP: Leap,
        PassiveSkill.FRENZY_CRY: FrenzyCry,
        PassiveSkill.RIPPER: Ripper,
        PassiveSkill.CLEAVE: Cleave,
        # String versions for compatibility
        "fast_frenzy": FastFrenzy,
        "hungry_frenzy": HungryFrenzy,
        "immortal_frenzy": ImmortalFrenzy,
        "leap": Leap,
        "frenzy_cry": FrenzyCry,
        "ripper": Ripper,
        "cleave": Cleave,
    }
    
    skill_class = skill_classes.get(skill_name)
    if skill_class:
        return skill_class()
    return None