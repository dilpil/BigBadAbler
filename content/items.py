import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from status_effect import DamageOverTimeEffect, StatModifierEffect, StackType
from projectile import Projectile
from constants import FRAME_TIME
import math

class Item:
    def __init__(self, name: str, description: str, cost: int):
        self.name = name
        self.description = description
        self.cost = cost
        self.stats = {}
        self.unit = None
        
    def apply_to_unit(self, unit):
        self.unit = unit
        for stat, value in self.stats.items():
            if hasattr(unit, stat):
                current_val = getattr(unit, stat)
                if stat in ["max_hp"]:
                    # Percentage increase for max_hp if value > 1
                    if "percent_hp" in self.stats:
                        setattr(unit, stat, int(current_val * (1 + self.stats["percent_hp"])))
                    else:
                        setattr(unit, stat, current_val + value)
                    # Update current HP when max HP changes
                    unit.hp = min(unit.hp + value, unit.max_hp)
                else:
                    setattr(unit, stat, current_val + value)
                
    def remove_from_unit(self, unit):
        for stat, value in self.stats.items():
            if hasattr(unit, stat):
                if stat in ["max_hp"] and "percent_hp" in self.stats:
                    current_val = getattr(unit, stat)
                    setattr(unit, stat, int(current_val / (1 + self.stats["percent_hp"])))
                else:
                    setattr(unit, stat, getattr(unit, stat) - value)
        self.unit = None
                
    def on_event(self, event_type: str, **kwargs):
        pass
    
    def on_frame(self, dt: float):
        pass


class FrenzyMask(Item):
    def __init__(self):
        super().__init__("Frenzy Mask", "On attack: +5% attack speed, +10 armor", 45)
        self.stats = {"armor": 10}
        self.stacks = 0
        self.applied_attack_speed = 0  # Track how much attack speed we've added
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            self.stacks += 1
            # Add 5 attack speed and track it
            self.unit.attack_speed += 5
            self.applied_attack_speed += 5
    
    def remove_from_unit(self, unit):
        # Remove all applied attack speed bonuses before calling parent method
        if hasattr(self, 'applied_attack_speed'):
            unit.attack_speed -= self.applied_attack_speed
            self.applied_attack_speed = 0
        self.stacks = 0
        super().remove_from_unit(unit)
    
    def apply_to_unit(self, unit):
        # Reset tracking when applied to a new unit
        self.applied_attack_speed = 0
        self.stacks = 0
        super().apply_to_unit(unit)
            

class Thrumblade(Item):
    def __init__(self):
        super().__init__("Thrumblade", "Every second: +5 attack damage, +10% max HP", 50)
        self.stats = {"max_hp": 0, "percent_hp": 0.1}
        self.timer = 0
        self.applied_attack_damage = 0  # Track how much attack damage we've added
        
    def on_frame(self, dt: float):
        if self.unit:
            self.timer += dt
            if self.timer >= 1.0:
                self.timer -= 1.0
                self.unit.attack_damage += 5
                self.applied_attack_damage += 5
    
    def remove_from_unit(self, unit):
        # Remove all applied attack damage bonuses before calling parent method
        if hasattr(self, 'applied_attack_damage'):
            unit.attack_damage -= self.applied_attack_damage
            self.applied_attack_damage = 0
        self.timer = 0
        super().remove_from_unit(unit)
    
    def apply_to_unit(self, unit):
        # Reset tracking when applied to a new unit
        self.applied_attack_damage = 0
        self.timer = 0
        super().apply_to_unit(unit)


class HammerOfBam(Item):
    def __init__(self):
        super().__init__("Hammer of Bam", "Every 3rd attack deals 300% damage, +20 damage", 55)
        self.stats = {"attack_damage": 20}
        self.attack_count = 0
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            self.attack_count += 1
            if self.attack_count >= 3:
                self.attack_count = 0
                # Triple the damage that was just dealt
                target = kwargs.get("target")
                damage = kwargs.get("damage", 0)
                if target and target.is_alive():
                    target.take_damage(damage * 2, "physical", self.unit)


class Manastaff(Item):
    def __init__(self):
        super().__init__("Manastaff", "+5 MP/s, on cast: projectile deals spell's mana cost as magic damage", 60)
        self.stats = {"mp_regen": 5}
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "spell_cast" and kwargs.get("caster") == self.unit:
            skill = kwargs.get("skill")
            if skill and hasattr(skill, "mana_cost") and skill.mana_cost:
                # Find nearest enemy
                if self.unit.board:
                    enemies = self.unit.board.get_enemy_units(self.unit.team)
                    if enemies:
                        nearest = min(enemies, key=lambda e: self.unit.board.get_distance(self.unit, e))
                        projectile = Projectile(self.unit, nearest, speed=15)
                        damage = skill.mana_cost
                        projectile.on_hit_callback = lambda target: target.take_damage(damage, "magical", self.unit)
                        self.unit.board.add_projectile(projectile)


class Burnmail(Item):
    def __init__(self):
        super().__init__("Burnmail", "+50 armor, +25 MR, deal 15 magic damage/s to enemies within 2 tiles", 70)
        self.stats = {"armor": 50, "magic_resist": 25}
        self.burn_timer = 0
        
    def on_frame(self, dt: float):
        if self.unit and self.unit.board:
            self.burn_timer += dt
            if self.burn_timer >= 1.0:
                self.burn_timer -= 1.0
                # Find enemies within 2 tiles
                enemies = self.unit.board.get_enemy_units(self.unit.team)
                for enemy in enemies:
                    if self.unit.board.get_distance(self.unit, enemy) <= 2:
                        enemy.take_damage(15, "magical", self.unit)


class ScorpionTail(Item):
    def __init__(self):
        super().__init__("Scorpion Tail", "+10 damage, on attack: inflict poison (5 damage/s)", 40)
        self.stats = {"attack_damage": 10}
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            target = kwargs.get("target")
            if target and target.is_alive():
                # Apply poison status effect
                poison = DamageOverTimeEffect("Poison", None, 5.0, "magical")
                poison.source = self.unit
                target.add_status_effect(poison)


class Phylactery(Item):
    def __init__(self):
        super().__init__("Phylactery", "Once per battle: at 50% HP, cleanse debuffs and heal to full", 80)
        self.triggered = False
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "damage_taken" and kwargs.get("unit") == self.unit:
            if not self.triggered and self.unit.hp <= self.unit.max_hp * 0.5:
                self.triggered = True
                # Cleanse all debuffs (properly remove to revert stat modifiers)
                for effect in self.unit.status_effects[:]:
                    effect.remove(self.unit)
                self.unit.status_effects.clear()
                # Heal to full
                old_hp = self.unit.hp
                self.unit.hp = self.unit.max_hp
                # Visual feedback
                self.unit.flash_color = (0, 255, 0)
                self.unit.flash_timer = 0.3
                self.unit.flash_duration = 0.3
                if self.unit.board:
                    self.unit.board.make_text_floater("Phylactery!", (255, 215, 0), unit=self.unit)


class Sunderer(Item):
    def __init__(self):
        super().__init__("Sunderer", "+20 damage, on hit: inflict sunder (-5 armor)", 45)
        self.stats = {"attack_damage": 20}
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            target = kwargs.get("target")
            if target and target.is_alive():
                # Apply sunder debuff (stacks infinitely)
                sunder = StatModifierEffect("Sunder", None, {"armor": -5}, StackType.STACK_INTENSITY)
                sunder.source = self.unit
                target.add_status_effect(sunder)


class Beastheart(Item):
    def __init__(self):
        super().__init__("Beastheart", "+500 max HP, +25% max HP", 65)
        self.stats = {"max_hp": 500}
        
    def apply_to_unit(self, unit):
        self.unit = unit
        # First add flat HP
        unit.max_hp += 500
        unit.hp += 500
        # Then multiply by 1.25
        unit.max_hp = int(unit.max_hp * 1.25)
        unit.hp = min(unit.hp, unit.max_hp)
        
    def remove_from_unit(self, unit):
        # Reverse the multiplication first
        unit.max_hp = int(unit.max_hp / 1.25)
        # Then remove flat HP
        unit.max_hp -= 500
        unit.hp = min(unit.hp, unit.max_hp)
        self.unit = None


class PhantomSaber(Item):
    def __init__(self):
        super().__init__("Phantom Saber", "+10 all combat stats, spawns 2 clones at battle start", 90)
        self.stats = {"attack_damage": 10, "armor": 10, "magic_resist": 10, "attack_speed": 10}
        self.clones_spawned = False
        
    def on_event(self, event_type: str, **kwargs):
        # We'll spawn clones at the first frame of combat
        if not self.clones_spawned and self.unit and self.unit.board:
            self.spawn_clones()
            
    def spawn_clones(self):
        if self.clones_spawned or not self.unit or not self.unit.board:
            return
            
        self.clones_spawned = True
        
        # Find positions for clones
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        positions_found = []
        
        for dx, dy in directions:
            x, y = self.unit.x + dx, self.unit.y + dy
            if self.unit.board.is_valid_position(x, y) and not self.unit.board.get_unit_at(x, y):
                positions_found.append((x, y))
                if len(positions_found) >= 2:
                    break
        
        # Create clones
        for i, (x, y) in enumerate(positions_found[:2]):
            # Import here to avoid circular dependency
            from content.unit_registry import create_unit
            
            clone = create_unit(self.unit.unit_type)
            if clone:
                clone.name = f"{self.unit.name} Clone"
                
                # Copy stats but reduce damage and HP
                clone.max_hp = int(self.unit.max_hp * 0.5)
                clone.hp = clone.max_hp
                clone.attack_damage = int(self.unit.attack_damage * 0.5)
                clone.armor = self.unit.armor
                clone.magic_resist = self.unit.magic_resist
                clone.attack_speed = self.unit.attack_speed
                clone.attack_range = self.unit.attack_range
                
                # Mark as summoned
                clone.is_summoned = True
                clone.summoner = self.unit
                
                # Add to board
                self.unit.board.add_unit(clone, x, y, self.unit.team)


class SnowGlobe(Item):
    def __init__(self):
        super().__init__("Snow Globe", "+20 int, +1 MP/s, on magic damage: apply chill (-3% AS/MS)", 50)
        self.stats = {"intelligence": 20, "mp_regen": 1}
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "damage_taken" and kwargs.get("source") == self.unit:
            from unit import DamageType
            damage_types = kwargs.get("damage_types", [])
            # Trigger on any non-physical magical damage
            non_phys = any(dt != DamageType.PHYSICAL for dt in damage_types)
            if non_phys:
                target = kwargs.get("unit")
                if target and target.is_alive():
                    chill = StatModifierEffect("Chill", None, {"attack_speed": -3, "move_speed": -0.03})
                    chill.source = self.unit
                    target.add_status_effect(chill)


class Echostone(Item):
    def __init__(self):
        super().__init__("Echostone", "On casting an ability, cast it again at 50% int", 75)
        self.echo_pending = False
        self.echoed_skill = None
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "spell_cast" and kwargs.get("caster") == self.unit:
            if not self.echo_pending:  # Prevent infinite recursion
                skill = kwargs.get("skill")
                if skill and not skill.is_passive:
                    self.echo_pending = True
                    self.echoed_skill = skill
                    # Store original int
                    original_int = self.unit.intelligence
                    # Reduce int by 50%
                    self.unit.intelligence = int(original_int * 0.5)
                    # Cast again (will happen next frame)
                    if hasattr(skill, 'execute'):
                        skill.execute(self.unit)
                    # Restore int
                    self.unit.intelligence = original_int
                    self.echo_pending = False


class Ominstone(Item):
    def __init__(self):
        super().__init__("Ominstone", "+20 all combat stats, +2 MP/s", 100)
        self.stats = {
            "attack_damage": 20,
            "intelligence": 20,
            "armor": 20,
            "magic_resist": 20,
            "attack_speed": 20,
            "mp_regen": 2
        }


class RedWaveblade(Item):
    def __init__(self):
        super().__init__("Red Waveblade", "+30 attack damage, +30 attack speed", 55)
        self.stats = {"attack_damage": 30, "attack_speed": 30}


class BlueWaveblade(Item):
    def __init__(self):
        super().__init__("Blue Waveblade", "+30 intelligence, +30 attack speed", 55)
        self.stats = {"intelligence": 30, "attack_speed": 30}


class NegationHelm(Item):
    def __init__(self):
        super().__init__("Negation Helm", "+60 magic resist, +4 MP/s", 60)
        self.stats = {"magic_resist": 60, "mp_regen": 4}


class ArmorOfTime(Item):
    def __init__(self):
        super().__init__("Armor of Time", "+10 armor/MR, +2 armor/MR per second", 65)
        self.stats = {"armor": 10, "magic_resist": 10}
        self.timer = 0
        self.applied_armor = 0  # Track how much armor we've added
        self.applied_magic_resist = 0  # Track how much MR we've added
        
    def on_frame(self, dt: float):
        if self.unit:
            self.timer += dt
            if self.timer >= 1.0:
                self.timer -= 1.0
                self.unit.armor += 2
                self.unit.magic_resist += 2
                self.applied_armor += 2
                self.applied_magic_resist += 2
    
    def remove_from_unit(self, unit):
        # Remove all applied bonuses before calling parent method
        if hasattr(self, 'applied_armor'):
            unit.armor -= self.applied_armor
            self.applied_armor = 0
        if hasattr(self, 'applied_magic_resist'):
            unit.magic_resist -= self.applied_magic_resist
            self.applied_magic_resist = 0
        self.timer = 0
        super().remove_from_unit(unit)
    
    def apply_to_unit(self, unit):
        # Reset tracking when applied to a new unit
        self.applied_armor = 0
        self.applied_magic_resist = 0
        self.timer = 0
        super().apply_to_unit(unit)


# ===== NEW ITEMS (converted from unit upgrades) =====

class ThunderGloves(Item):
    """Melee attacks deal bonus lightning damage"""
    def __init__(self):
        super().__init__("Thunder Gloves", "+65 lightning damage on melee attacks", 45)
        self.bonus_damage = 65

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            target = kwargs.get("target")
            # Only trigger for melee attacks
            if target and target.is_alive() and self.unit.attack_range <= 1:
                target.take_damage(self.bonus_damage, "lightning", self.unit)


class LeapBoots(Item):
    """On kill, leap to lowest HP enemy within 3 tiles"""
    def __init__(self):
        super().__init__("Leap Boots", "On kill, leap to lowest HP enemy within 3 tiles", 50)

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_death" and kwargs.get("killer") == self.unit:
            self.perform_leap()

    def perform_leap(self):
        if not self.unit or not self.unit.board:
            return

        # Find lowest HP enemy within 3 tiles
        enemies = self.unit.board.get_enemy_units(self.unit.team)
        valid_targets = []

        for enemy in enemies:
            distance = self.unit.board.get_distance(self.unit, enemy)
            if distance <= 3 and enemy.is_alive():
                valid_targets.append(enemy)

        if not valid_targets:
            return

        # Find lowest HP target
        target = min(valid_targets, key=lambda e: e.hp)

        # Find adjacent position to leap to
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dx, dy in directions:
            x, y = target.x + dx, target.y + dy
            if self.unit.board.is_valid_position(x, y) and not self.unit.board.get_unit_at(x, y):
                self.unit.board.move_unit(self.unit, x, y)
                break


class ArmorShredder(Item):
    """Attacks permanently reduce target armor"""
    def __init__(self):
        super().__init__("Armor Shredder", "Attacks permanently reduce target armor by 1", 40)

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            target = kwargs.get("target")
            if target and target.is_alive():
                target.armor = max(0, target.armor - 1)


class CleavingBlade(Item):
    """Attacks hit adjacent enemies"""
    def __init__(self):
        super().__init__("Cleaving Blade", "Attacks also hit up to 3 adjacent enemies", 55)

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            primary_target = kwargs.get("target")
            self.perform_cleave(primary_target)

    def perform_cleave(self, primary_target):
        if not self.unit or not self.unit.board or not primary_target:
            return

        # Find adjacent enemies to primary target
        enemies = self.unit.board.get_enemy_units(self.unit.team)
        cleave_targets = []

        for enemy in enemies:
            if enemy != primary_target and enemy.is_alive():
                distance = self.unit.board.get_distance(primary_target, enemy)
                if distance <= 1:
                    cleave_targets.append(enemy)

        # Hit up to 3 adjacent enemies
        for target in cleave_targets[:3]:
            damage = self.unit.attack_damage
            if self.unit.strength > 0:
                damage *= (1 + self.unit.strength / 100.0)
            target.take_damage(damage, "physical", self.unit)


class FireStaff(Item):
    """Attacks deal bonus fire damage based on INT"""
    def __init__(self):
        super().__init__("Fire Staff", "Attacks deal additional fire damage equal to Intelligence", 45)

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            target = kwargs.get("target")
            if target and target.is_alive():
                fire_damage = getattr(self.unit, 'intelligence', 0)
                if fire_damage > 0:
                    target.take_damage(fire_damage, "fire", self.unit)


class HealingBlade(Item):
    """On hit, heal nearest ally"""
    def __init__(self):
        super().__init__("Healing Blade", "On hit, heal nearest ally for 50 HP", 50)
        self.heal_amount = 50

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            damage = kwargs.get("damage", 0)
            if damage > 0 and self.unit.board:
                import random
                allies = self.unit.board.get_allied_units(self.unit.team)
                injured_allies = [a for a in allies if a.is_alive() and a.hp < a.max_hp]

                if injured_allies:
                    # Find nearest ally
                    nearest_dist = min(self.unit.board.get_distance(self.unit, a) for a in injured_allies)
                    nearest_allies = [a for a in injured_allies
                                     if self.unit.board.get_distance(self.unit, a) == nearest_dist]
                    target_ally = random.choice(nearest_allies)
                    target_ally.heal(self.heal_amount, self.unit)


class CloakOfShadows(Item):
    """Gain dodge stacks over time"""
    def __init__(self):
        super().__init__("Cloak of Shadows", "Gain 1 dodge every 2 seconds", 55)
        self.dodge_timer = 0
        self.dodge_interval = 2.0

    def on_frame(self, dt: float):
        if not self.unit or not self.unit.is_alive():
            return

        self.dodge_timer += dt
        if self.dodge_timer >= self.dodge_interval:
            self.dodge_timer -= self.dodge_interval

            # Check if unit already has dodge effect
            existing_dodge = None
            for effect in self.unit.status_effects:
                if effect.name == "Dodge":
                    existing_dodge = effect
                    break

            if existing_dodge and hasattr(existing_dodge, 'stacks'):
                existing_dodge.stacks += 1
            else:
                # Create new dodge effect
                from status_effect import DodgeEffect
                dodge = DodgeEffect(1)
                dodge.source = self.unit
                self.unit.add_status_effect(dodge)


class ThrowingKnives(Item):
    """Attacks hit another random enemy"""
    def __init__(self):
        super().__init__("Throwing Knives", "Attacks also hit another random enemy within 3 tiles", 40)
        self._throwing = False  # Reentrancy guard

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            if self._throwing:
                return  # Prevent reentrant calls
            primary_target = kwargs.get("target")
            self.throw_knife(primary_target, kwargs.get("damage", 0))

    def throw_knife(self, primary_target, original_damage):
        import random
        if not self.unit or not self.unit.board:
            return

        self._throwing = True
        try:
            enemies = self.unit.board.get_enemy_units(self.unit.team)
            potential_targets = []

            for enemy in enemies:
                if (enemy.is_alive() and enemy != primary_target and
                    self.unit.board.get_distance(self.unit, enemy) <= 3):
                    potential_targets.append(enemy)

            if potential_targets:
                knife_target = random.choice(potential_targets)
                # Use 75% of original attack damage, not current attack_damage stat
                knife_damage = original_damage * 0.75 if original_damage > 0 else self.unit.attack_damage * 0.75
                knife_target.take_damage(knife_damage, "physical", self.unit)
        finally:
            self._throwing = False


class VenomousBlade(Item):
    """Attacks apply poison"""
    def __init__(self):
        super().__init__("Venomous Blade", "Attacks apply poison (15 damage/s for 10s)", 35)

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            target = kwargs.get("target")
            if target and target.is_alive():
                from status_effect import PoisonEffect
                poison = PoisonEffect(10.0, 15.0)
                poison.source = self.unit
                target.add_status_effect(poison)


class CriticalEdge(Item):
    """Every 4th attack deals triple damage"""
    def __init__(self):
        super().__init__("Critical Edge", "Every 4th attack deals 3x damage", 50)
        self.attack_count = 0

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            self.attack_count += 1
            if self.attack_count >= 4:
                self.attack_count = 0
                target = kwargs.get("target")
                damage = kwargs.get("damage", 0)
                if target and target.is_alive() and damage > 0:
                    # Deal 2x extra damage (for 3x total)
                    target.take_damage(damage * 2, "physical", self.unit)


class BasiliskHammer(Item):
    """On attack, deal physical damage equal to wielder's armor + resist"""
    def __init__(self):
        super().__init__("Basilisk Hammer", "On attack: deal physical damage equal to your armor + magic resist", 55)
        self.stats = {"attack_damage": 15}

    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and kwargs.get("attacker") == self.unit:
            target = kwargs.get("target")
            if target and target.is_alive() and self.unit:
                bonus_damage = self.unit.armor + self.unit.magic_resist
                if bonus_damage > 0:
                    target.take_damage(bonus_damage, "physical", self.unit)


class FrostyCloak(Item):
    """Enemies within 3 tiles are chilled (reduced attack speed and move speed)"""
    def __init__(self):
        super().__init__("Frosty Cloak", "Enemies within 3 tiles are chilled (-15% attack speed, -20% move speed)", 50)
        self.stats = {"armor": 20, "magic_resist": 20}
        self.tick_timer = 0
        self.tick_interval = 1.0
        self.range = 3

    def on_frame(self, dt: float):
        if not self.unit or not self.unit.board or not self.unit.is_alive():
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            self.apply_chill()

    def apply_chill(self):
        from status_effect import StatModifierEffect
        enemies = self.unit.board.get_enemy_units(self.unit.team)
        for enemy in enemies:
            if enemy.is_alive():
                distance = self.unit.board.get_distance(self.unit, enemy)
                if distance <= self.range:
                    # Check if already chilled by this item
                    has_chill = any(e.name == "Frosty Chill" for e in enemy.status_effects)
                    if not has_chill:
                        chill = StatModifierEffect(
                            "Frosty Chill",
                            2.0,  # 2 second duration, reapplied every second
                            {"attack_speed": -15, "move_speed": -0.4}
                        )
                        chill.source = self.unit
                        enemy.add_status_effect(chill)


def create_item(item_name: str) -> Item:
    item_classes = {
        "frenzy_mask": FrenzyMask,
        "thrumblade": Thrumblade,
        "hammer_of_bam": HammerOfBam,
        "manastaff": Manastaff,
        "burnmail": Burnmail,
        "scorpion_tail": ScorpionTail,
        "phylactery": Phylactery,
        "sunderer": Sunderer,
        "beastheart": Beastheart,
        "phantom_saber": PhantomSaber,
        "snow_globe": SnowGlobe,
        "echostone": Echostone,
        "ominstone": Ominstone,
        "red_waveblade": RedWaveblade,
        "blue_waveblade": BlueWaveblade,
        "negation_helm": NegationHelm,
        "armor_of_time": ArmorOfTime,
        # New items (converted from unit upgrades)
        "thunder_gloves": ThunderGloves,
        "leap_boots": LeapBoots,
        "armor_shredder": ArmorShredder,
        "cleaving_blade": CleavingBlade,
        "fire_staff": FireStaff,
        "healing_blade": HealingBlade,
        "cloak_of_shadows": CloakOfShadows,
        "throwing_knives": ThrowingKnives,
        "venomous_blade": VenomousBlade,
        "critical_edge": CriticalEdge,
        "basilisk_hammer": BasiliskHammer,
        "frosty_cloak": FrostyCloak,
    }

    item_class = item_classes.get(item_name.lower().replace(" ", "_"))
    if item_class:
        return item_class()
    return None


def get_all_items():
    return [
        "frenzy_mask",
        "thrumblade",
        "hammer_of_bam",
        "manastaff",
        "burnmail",
        "scorpion_tail",
        "phylactery",
        "sunderer",
        "beastheart",
        "phantom_saber",
        "snow_globe",
        "echostone",
        "ominstone",
        "red_waveblade",
        "blue_waveblade",
        "negation_helm",
        "armor_of_time",
        # New items
        "thunder_gloves",
        "leap_boots",
        "armor_shredder",
        "cleaving_blade",
        "fire_staff",
        "healing_blade",
        "cloak_of_shadows",
        "throwing_knives",
        "venomous_blade",
        "critical_edge",
        "basilisk_hammer",
        "frosty_cloak",
    ]


def generate_item_shop(count: int = 10) -> list:
    import random
    all_items = get_all_items()
    # Allow duplicates since we have more items than shop slots
    selected_items = random.choices(all_items, k=min(count, len(all_items)))
    return [create_item(item_name) for item_name in selected_items]