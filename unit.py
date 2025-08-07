from enum import Enum
from typing import List, Optional
import math

class UnitState(Enum):
    IDLE = "idle"
    WALKING = "walking"
    ATTACKING = "attacking"
    CASTING = "casting"

class UnitType(Enum):
    NECROMANCER = "necromancer"
    PALADIN = "paladin"
    PYROMANCER = "pyromancer"
    BERSERKER = "berserker"
    SKELETON = "skeleton"

class Unit:
    _next_id = 0
    
    def __init__(self, name: str, unit_type: UnitType):
        self.id = Unit._next_id
        Unit._next_id += 1
        self.name = name
        self.unit_type = unit_type
        self.team = None
        self.x = 0
        self.y = 0
        self.original_x = 0
        self.original_y = 0
        
        self.max_hp = 100
        self.hp = self.max_hp
        self.hp_regen = 1.0
        
        self.mp_regen = 0.0  # Mana regen for spell, defaults to 0
        
        self.strength = 0
        self.intelligence = 0
        self.armor = 0
        self.magic_resist = 0
        
        self.attack_damage = 10
        self.attack_range = 1
        self.attack_speed = 0
        self.base_attack_time = 1.0
        self.attack_timer = 0
        
        self.spell = None
        self.passive_skills = []  # List of passive skills
        self.items = []
        self.status_effects = []
        
        self.state = UnitState.IDLE
        self.target = None
        self.cast_skill = None
        self.cast_timer = 0
        self.cast_time = 0
        
        self.move_timer = 0
        self.move_speed = 2.0
        
        self.board = None
        self.is_summoned = False
        self.summoner = None
        
        # Visual effects
        self.flash_timer = 0
        self.flash_color = None
        self.flash_duration = 0
        self.bump_timer = 0
        self.bump_direction = (0, 0)
        self.death_timer = 0
        self.cast_jump_timer = 0
        
    def is_alive(self) -> bool:
        return self.hp > 0
    
    def can_attack(self, target) -> bool:
        if not self.is_alive() or not target.is_alive():
            return False
        if self.state != UnitState.IDLE:
            return False
        if self.attack_timer > 0:
            return False
        
        distance = self.board.get_distance(self, target)
        return distance <= self.attack_range
    
    def attack(self, target):
        if not self.can_attack(target):
            return
            
        self.state = UnitState.ATTACKING
        self.target = target
        
        damage = self.attack_damage * (1 + self.strength / 100)
        
        attack_time = self.base_attack_time / (1 + self.attack_speed / 100)
        self.attack_timer = attack_time
        
        # Grant mana to spell on attack
        if self.spell and self.state != UnitState.CASTING:
            self.spell.add_mana(10)
        
        # Check if this is a ranged attack
        distance = self.board.get_distance(self, target)
        if distance > 1:  # Ranged attack - create projectile
            from projectile import Projectile
            projectile = Projectile(self, target, speed=15.0)
            projectile.damage = damage
            projectile.damage_type = "physical"
            projectile.on_hit_callback = lambda tgt: tgt.take_damage(projectile.damage, projectile.damage_type, self)
            self.board.add_projectile(projectile)
        else:  # Melee attack - direct damage
            target.take_damage(damage, "physical", self)
        
        # Visual effect - bump towards target
        dx = target.x - self.x
        dy = target.y - self.y
        if dx != 0:
            dx = dx / abs(dx)
        if dy != 0:
            dy = dy / abs(dy)
        self.bump_direction = (dx * 0.6, dy * 0.6)
        self.bump_timer = 0.3
        
        self.board.raise_event("unit_attack", attacker=self, target=target, damage=damage)
    
    def take_damage(self, amount: float, damage_type: str, source):
        if not self.is_alive():
            return
            
        # Grant mana based on pre-mitigation damage
        if self.spell and self.state != UnitState.CASTING:
            self.spell.add_mana(amount * 0.02)
            
        if damage_type == "physical":
            mitigation = 100 / (100 + self.armor)
        elif damage_type == "magical":
            mitigation = 100 / (100 + self.magic_resist)
        else:
            mitigation = 1.0
            
        actual_damage = amount * mitigation
        self.hp -= actual_damage
        
        # Visual effect - white flash on damage
        self.flash_color = (255, 255, 255)
        self.flash_timer = 0.2
        self.flash_duration = 0.2
        
        # Text floater for damage
        if damage_type == "physical":
            damage_color = (255, 255, 255)  # White for physical damage
        elif damage_type == "magical":
            damage_color = (173, 216, 230)  # Light blue for magical damage
        else:
            damage_color = (255, 255, 0)  # Yellow for other damage types
            
        self.board.make_text_floater(f"{int(actual_damage)}", damage_color, unit=self)
        
        # Add to combat log
        if self.board.game:
            source_name = source.name if hasattr(source, 'name') else "Unknown"
            self.board.game.add_message(f"{source_name} dealt {int(actual_damage)} {damage_type} damage to {self.name}")
        
        self.board.raise_event("damage_taken", 
                              unit=self, 
                              damage=actual_damage, 
                              damage_type=damage_type, 
                              source=source)
        
        if self.hp <= 0:
            self.hp = 0
            self.die(source)
            
        return actual_damage
    
    def heal(self, amount: float, source):
        if not self.is_alive():
            return
            
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        actual_heal = self.hp - old_hp
        
        self.board.raise_event("unit_healed", unit=self, amount=actual_heal, source=source)
        return actual_heal
    
    def die(self, killer):
        # Visual effect - red flash 4 times before vanishing
        self.death_timer = 0.8  # 4 flashes over 0.8 seconds
        self.flash_color = (255, 0, 0)
        
        # Add to combat log
        if self.board.game:
            killer_name = killer.name if hasattr(killer, 'name') else "Unknown"
            self.board.game.add_message(f"{self.name} is slain by {killer_name}")
        
        # Add corpse to the board for necromancer abilities
        self.board.add_corpse(self.x, self.y, self)
        
        self.board.raise_event("unit_death", unit=self, killer=killer)
        self.board.raise_event("death", dying_unit=self, killer=killer)
    
    def can_cast(self, skill) -> bool:
        if not self.is_alive():
            return False
        if self.state != UnitState.IDLE:
            return False
        if skill.is_passive:
            return False
        if skill.is_on_cooldown():
            return False
        if not hasattr(skill, 'current_mana') or skill.current_mana < skill.mana_cost:
            return False
        return True
    
    def cast(self, skill):
        if not self.can_cast(skill):
            return False
            
        self.state = UnitState.CASTING
        self.cast_skill = skill
        self.cast_timer = 0
        self.cast_time = skill.cast_time
        
        # Visual effect - continuous purple glow during cast
        self.flash_color = (128, 0, 255)
        self.flash_timer = skill.cast_time  # Glow for entire cast duration
        self.flash_duration = skill.cast_time
        # Don't jump up immediately - will jump at cast completion
        
        # Text floater for beginning cast
        self.board.make_text_floater(f"Casting {skill.name}...", (128, 0, 255), unit=self)
        
        # Add to combat log
        if self.board.game:
            self.board.game.add_message(f"{self.name} begins casting {skill.name}")
        
        self.board.raise_event("spell_cast", caster=self, skill=skill)
        return True
    
    def try_cast_spell(self):
        if not self.spell or self.spell.is_passive:
            return False
        if self.can_cast(self.spell) and self.spell.should_cast(self):
            return self.cast(self.spell)
        return False
    
    def update(self, dt: float):
        # Update visual effects
        if self.flash_timer > 0:
            self.flash_timer -= dt
            
        if self.bump_timer > 0:
            self.bump_timer -= dt
            
        if self.cast_jump_timer > 0:
            self.cast_jump_timer -= dt
            
        if self.death_timer > 0:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.board.remove_unit(self)
                return
                
        if not self.is_alive():
            return
            
        self.hp = min(self.hp + self.hp_regen * dt, self.max_hp)
        
        # Add mp_regen to spell if not casting
        if self.spell and self.state != UnitState.CASTING:
            self.spell.add_mana(self.mp_regen * dt)
        
        if self.attack_timer > 0:
            self.attack_timer -= dt
            
        # Update all skills
        for skill in self.iter_skills():
            skill.update(dt)
            
        for status in self.status_effects[:]:
            status.update(dt)
            if status.is_expired():
                self.remove_status_effect(status)
                
        if self.state == UnitState.CASTING:
            self.cast_timer += dt
            if self.cast_timer >= self.cast_time:
                # Visual effect - bump up when cast completes
                self.cast_jump_timer = 0.3
                
                # Text floater for completing cast
                self.board.make_text_floater(f"Casts {self.cast_skill.name}!", (128, 0, 255), unit=self)
                
                # Add to combat log
                if self.board.game:
                    self.board.game.add_message(f"{self.name} casts {self.cast_skill.name}!")
                
                self.cast_skill.execute(self)
                self.cast_skill.current_mana = 0  # Reset mana after casting
                self.state = UnitState.IDLE
                self.cast_skill = None
                
        elif self.state == UnitState.ATTACKING:
            self.state = UnitState.IDLE
            
        elif self.state == UnitState.WALKING:
            self.move_timer -= dt
            if self.move_timer <= 0:
                self.state = UnitState.IDLE
                
        if self.state == UnitState.IDLE:
            # Don't take any actions while attack is on cooldown
            if self.attack_timer > 0:
                return
                
            if self.try_cast_spell():
                return
                
            if self.target and self.target.is_alive() and self.can_attack(self.target):
                self.attack(self.target)
                return
                
            # Check if we can attack any enemy in range first
            enemies = self.board.enemy_units if self.team == "player" else self.board.player_units
            enemies_in_range = [enemy for enemy in enemies if enemy.is_alive() and self.can_attack(enemy)]
            
            if enemies_in_range:
                # Attack the first enemy in range
                self.attack(enemies_in_range[0])
            else:
                # For ranged units, check if any enemies are within attack range before moving
                enemies_in_attack_range = [enemy for enemy in enemies if enemy.is_alive() and 
                                         self.board.get_distance(self, enemy) <= self.attack_range]
                
                if not enemies_in_attack_range:
                    # Only move if no enemies are within attack range
                    nearest_enemy = self.board.get_nearest_enemy(self)
                    if nearest_enemy:
                        self.move_towards(nearest_enemy)
    
        
    def move_towards(self, target):
        if self.state != UnitState.IDLE:
            return
            
        path = self.board.find_path(self.x, self.y, target.x, target.y)
        if len(path) > 1:
            next_pos = path[1]
            if self.board.move_unit(self, next_pos[0], next_pos[1]):
                self.state = UnitState.WALKING
                self.move_timer = 1.0 / self.move_speed
    
    def reset(self):
        """Reset unit to fresh state for new round."""
        # Basic stats
        self.hp = self.max_hp
        self.status_effects.clear()
        
        # Reset spell mana
        if self.spell:
            self.spell.current_mana = 0
            
        # Reset passive skills (they don't have mana but may need reset)
        for passive in self.passive_skills:
            if hasattr(passive, 'reset'):
                passive.reset()
        
        # Combat state
        self.target = None
        self.state = UnitState.IDLE
        self.attack_timer = 0
        
        # Casting state
        self.cast_skill = None
        self.cast_timer = 0
        self.cast_time = 0
        
        # Movement state
        self.move_timer = 0
        
        # Visual effects - IMPORTANT: Reset death timer!
        self.flash_timer = 0
        self.flash_color = None
        self.flash_duration = 0
        self.bump_timer = 0
        self.bump_direction = (0, 0)
        self.death_timer = 0  # This was the bug!
        self.cast_jump_timer = 0
        
        # Spells no longer have cooldowns
    
    def set_spell(self, spell):
        self.spell = spell
        if spell:
            spell.owner = self
            spell.current_mana = 0
        return True
    
    def add_passive_skill(self, skill):
        """Add a passive skill to the unit"""
        if skill and skill not in self.passive_skills:
            self.passive_skills.append(skill)
            skill.owner = self
            skill.apply_to_owner(self)
            return True
        return False
    
    def iter_skills(self):
        """Iterate over all skills - active spell first, then passive skills"""
        if self.spell:
            yield self.spell
        for passive in self.passive_skills:
            yield passive
    
    def add_item(self, item):
        if len(self.items) >= 3:
            return False
        self.items.append(item)
        item.apply_to_unit(self)
        return True
    
    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            item.remove_from_unit(self)
    
    def add_status_effect(self, status_effect):
        self.status_effects.append(status_effect)
        status_effect.apply(self)
    
    def remove_status_effect(self, status_effect):
        if status_effect in self.status_effects:
            self.status_effects.remove(status_effect)
            status_effect.remove(self)
    
    def get_total_stats(self):
        stats = {
            "hp": self.max_hp,
            "hp_regen": self.hp_regen,
            "mp_regen": self.mp_regen,
            "passive_skills": len(self.passive_skills),
            "strength": self.strength,
            "intelligence": self.intelligence,
            "armor": self.armor,
            "magic_resist": self.magic_resist,
            "attack_damage": self.attack_damage,
            "attack_range": self.attack_range,
            "attack_speed": self.attack_speed
        }
        
        for item in self.items:
            if hasattr(item, "stats"):
                for stat, value in item.stats.items():
                    if stat in stats:
                        stats[stat] += value
                        
        for status in self.status_effects:
            if hasattr(status, "stat_modifiers"):
                for stat, value in status.stat_modifiers.items():
                    if stat in stats:
                        stats[stat] += value
                        
        return stats
    
    # Unit-specific methods to be overridden by subclasses
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return []
    
    def get_passive_skill_cost(self, skill_name: str) -> int:
        """Get the cost of a passive skill"""
        return 30  # Default cost
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50  # Default cost