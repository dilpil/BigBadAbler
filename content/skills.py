import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill import Skill
from projectile import Projectile, AoEProjectile
from status_effect import *
from content.unit_registry import create_unit
from visual_effect import VisualEffectType

class SummonSkeleton(Skill):
    def __init__(self):
        super().__init__("Summon Skeleton", "Summons a skeleton warrior to fight for you")
        self.cast_time = 1.0
        self.mana_cost = 100
        self.summon_type = "skeleton"
        
    def should_cast(self, caster) -> bool:
        return len([u for u in caster.board.player_units if u.unit_type == "skeleton"]) < 3
        
    def execute(self, caster):
        pos = self.find_summon_position(caster)
        if pos:
            skeleton = self.create_summon(caster)
            
            # Check for Undead Horde upgrade (summons 2 skeletons instead of 1)
            num_skeletons = 2 if self.has_passive_skill("undead_horde") else 1
            
            for i in range(num_skeletons):
                if i > 0:
                    # Find another position for additional skeletons
                    pos = self.find_summon_position(caster)
                    if not pos:
                        break
                    skeleton = self.create_summon(caster)
                
                # Apply upgrades to the skeleton based on passive skills
                self.apply_skeleton_upgrades(caster, skeleton)
                
                # Use the summoning helper
                self.summon_minion(caster, skeleton, pos)
                
                # Add dark visual effect at the summoning location
                caster.board.add_visual_effect(VisualEffectType.DARK, pos[0], pos[1])
            
    def create_summon(self, caster):
        skeleton = create_unit("skeleton")
        if not skeleton:
            from unit import Unit
            skeleton = Unit("Skeleton", "skeleton")
            skeleton.max_hp = 40
            skeleton.hp = skeleton.max_hp
            skeleton.attack_damage = 8
            skeleton.armor = 5
        return skeleton
    
    def apply_skeleton_upgrades(self, caster, skeleton):
        """Apply passive skill upgrades to summoned skeletons"""
        # Bone Sabers - increased melee damage
        if self.has_passive_skill("bone_sabers"):
            skeleton.attack_damage += 5
            
        # Hunger - add life drain spell
        if self.has_passive_skill("hunger"):
            hunger_spell = LifeDrainSpell()
            skeleton.set_spell(hunger_spell)
            
        # Burning Bones - add fire aura
        if self.has_passive_skill("burning_bones"):
            fire_aura = BurningBonesAura()
            skeleton.add_passive_skill(fire_aura)


class HolyAura(Skill):
    def __init__(self):
        super().__init__("Holy Aura", "Heals nearby allies for 3 HP every second")
        self.heal_amount = 3.0
        self.range = 2
        self.tick_timer = 0
        
    def update(self, dt: float):
        super().update(dt)
        if not self.owner or not self.owner.is_alive():
            return
            
        self.tick_timer += dt
        if self.tick_timer >= 1.0:
            self.tick_timer -= 1.0
            allies = self.owner.board.get_units_in_range(self.owner.x, self.owner.y, self.range, self.owner.team)
            for ally in allies:
                if ally.is_alive():
                    ally.heal(self.heal_amount, self.owner)


class Fireball(Skill):
    def __init__(self):
        super().__init__("Fireball", "Launches an explosive fireball at the nearest enemy")
        self.cast_time = 0.8
        self.mana_cost = 100
        self.range = 6
        self.aoe_radius = 2
        self.damage = 40
        
    def should_cast(self, caster) -> bool:
        return len(self.get_valid_targets(caster, "enemy")) > 0
        
    def execute(self, caster):
        targets = self.get_valid_targets(caster, "enemy")
        if targets:
            target = targets[0]  # Use first valid target
            projectile = AoEProjectile(caster, target.x, target.y, speed=8.0)
            projectile.damage = self.damage * (1 + caster.intelligence / 100)
            projectile.damage_type = "magical"
            projectile.explosion_radius = self.aoe_radius
            caster.board.add_projectile(projectile)


class Bloodlust(Skill):
    def __init__(self):
        super().__init__("Bloodlust", "Increases attack speed by 50% for 3 seconds")
        self.cast_time = 0.5
        self.mana_cost = 100
        self.range = 0
        self.duration = 3.0
        self.attack_speed_bonus = 50
        
    def should_cast(self, caster) -> bool:
        return not any(e.name == "Bloodlust" for e in caster.status_effects)
        
    def execute(self, caster):
        effect = StatModifierEffect("Bloodlust", self.duration, {"attack_speed": self.attack_speed_bonus})
        effect.source = caster
        caster.add_status_effect(effect)


# ===== NECROMANCER PASSIVE SKILLS =====

class Hunger(Skill):
    """Summoned skeletons gain a ranged life drain spell"""
    def __init__(self):
        super().__init__("Hunger", "Summoned skeletons gain a ranged life drain spell")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

class BoneShards(Skill):
    """On death, summoned skeletons shoot bone shards at the 3 nearest enemies"""
    def __init__(self):
        super().__init__("Bone Shards", "On death, summoned skeletons shoot bone shards at the 3 nearest enemies")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "death" and "dying_unit" in kwargs:
            dying_unit = kwargs["dying_unit"]
            # Only trigger for summoned skeletons
            if (dying_unit.unit_type == "skeleton" and 
                hasattr(dying_unit, 'is_summoned') and dying_unit.is_summoned):
                self.shoot_bone_shards(dying_unit)
                
    def shoot_bone_shards(self, skeleton):
        """Shoot bone shards at 3 nearest enemies"""
        enemies = self.get_valid_targets(skeleton, "enemy", max_range=8)
        enemies.sort(key=lambda e: skeleton.board.get_distance(skeleton, e))
        
        for i, enemy in enumerate(enemies[:3]):
            projectile = Projectile(skeleton, enemy, speed=12.0)
            projectile.damage = 15
            projectile.damage_type = "physical"
            projectile.on_hit_callback = lambda tgt: tgt.take_damage(projectile.damage, projectile.damage_type, skeleton)
            skeleton.board.add_projectile(projectile)

class UndeadHorde(Skill):
    """Summons 2 skeletons instead of 1"""
    def __init__(self):
        super().__init__("Undead Horde", "Summons 2 skeletons instead of 1")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

class BurningBones(Skill):
    """Summoned Skeletons have a radius 2 fire damage aura"""
    def __init__(self):
        super().__init__("Burning Bones", "Summoned Skeletons have a radius 2 fire damage aura")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

class BurningBonesAura(Skill):
    """Fire aura that gets applied to skeletons"""
    def __init__(self):
        super().__init__("Fire Aura", "Deals fire damage to nearby enemies")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.damage = 8
        self.range = 2
        self.tick_timer = 0
        
    def update(self, dt: float):
        super().update(dt)
        if not self.owner or not self.owner.is_alive():
            return
            
        self.tick_timer += dt
        if self.tick_timer >= 1.0:
            self.tick_timer -= 1.0
            enemies = self.get_targets_in_area(self.owner, self.owner.x, self.owner.y, self.range, "enemy")
            for enemy in enemies:
                if enemy.is_alive():
                    enemy.take_damage(self.damage, "magical", self.owner)

class GraveChill(Skill):
    """When an enemy unit dies, deal ice damage to a random nearby enemy"""
    def __init__(self):
        super().__init__("Grave Chill", "When an enemy unit dies, deal ice damage equal to 5% of that enemies max hp to a random nearby enemy")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "death" and "dying_unit" in kwargs:
            dying_unit = kwargs["dying_unit"]
            # Only trigger for enemy units (from owner's perspective)
            if dying_unit.team != self.owner.team:
                self.apply_grave_chill(dying_unit)
                
    def apply_grave_chill(self, dying_unit):
        """Deal ice damage to a random nearby enemy"""
        import random
        
        # Find enemies near the dying unit
        nearby_enemies = self.get_targets_in_area(dying_unit, dying_unit.x, dying_unit.y, 3, "enemy")
        # Filter out the dying unit itself
        nearby_enemies = [e for e in nearby_enemies if e != dying_unit and e.is_alive()]
        
        if nearby_enemies:
            target = random.choice(nearby_enemies)
            damage = dying_unit.max_hp * 0.05
            target.take_damage(damage, "magical", self.owner)

class BoneFragments(Skill):
    """Summoned Skeletons spawn bone fragments on death"""
    def __init__(self):
        super().__init__("Bone Fragments", "Summoned Skeletons spawn bone fragments on death, which are smaller undead minions")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "death" and "dying_unit" in kwargs:
            dying_unit = kwargs["dying_unit"]
            # Only trigger for summoned skeletons
            if (dying_unit.unit_type == "skeleton" and 
                hasattr(dying_unit, 'is_summoned') and dying_unit.is_summoned):
                self.spawn_bone_fragment(dying_unit)
                
    def spawn_bone_fragment(self, skeleton):
        """Spawn a bone fragment at the skeleton's location"""
        # Create bone fragment unit
        fragment = create_unit("bone_fragment")
        if not fragment:
            from unit import Unit
            fragment = Unit("Bone Fragment", "bone_fragment")
            fragment.max_hp = 15
            fragment.hp = fragment.max_hp
            fragment.attack_damage = 3
            fragment.armor = 2
            fragment.attack_range = 1
            
        # Place at skeleton's position
        if not skeleton.board.get_unit_at(skeleton.x, skeleton.y):
            self.summon_minion(skeleton.summoner if hasattr(skeleton, 'summoner') else self.owner, 
                             fragment, (skeleton.x, skeleton.y))

class BoneSabers(Skill):
    """Skeletons melee damage is increased"""
    def __init__(self):
        super().__init__("Bone Sabers", "Skeletons melee damage is increased")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0

class LifeDrainSpell(Skill):
    """Life drain spell for skeletons with Hunger upgrade"""
    def __init__(self):
        super().__init__("Life Drain", "Drains life from enemies")
        self.cast_time = 1.0
        self.mana_cost = 50
        self.range = 4
        self.damage = 12
        
    def should_cast(self, caster) -> bool:
        return len(self.get_valid_targets(caster, "enemy")) > 0
        
    def execute(self, caster):
        targets = self.get_valid_targets(caster, "enemy")
        if targets:
            target = targets[0]
            damage_dealt = target.take_damage(self.damage, "magical", caster)
            # Heal the caster for half the damage dealt
            caster.heal(damage_dealt * 0.5, caster)

def create_skill(skill_name: str) -> Skill:
    skill_classes = {
        "summon_skeleton": SummonSkeleton,
        "holy_aura": HolyAura,
        "fireball": Fireball,
        "bloodlust": Bloodlust,
        # Necromancer passive skills
        "hunger": Hunger,
        "bone_shards": BoneShards,
        "undead_horde": UndeadHorde,
        "burning_bones": BurningBones,
        "grave_chill": GraveChill,
        "bone_fragments": BoneFragments,
        "bone_sabers": BoneSabers,
    }
    
    skill_class = skill_classes.get(skill_name.lower())
    if skill_class:
        return skill_class()
    return None

# Unit-specific functions moved to individual unit classes


def get_skill_cost(skill_name: str) -> int:
    return 25