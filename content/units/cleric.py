import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType, PassiveSkill
from skill import Skill
from status_effect import StatModifierEffect

class Cleric(Unit):
    def __init__(self):
        super().__init__("Cleric", UnitType.CLERIC)
        self.max_hp = 550
        self.hp = self.max_hp
        self.max_mp = 70
        self.mp = 0
        self.attack_damage = 40
        self.attack_range = 3  # Ranged unit
        self.attack_speed = -20  # 0.8 attacks per second
        self.strength = 5
        self.armor = 20
        self.magic_resist = 30
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_cleric_skill("heal")
        if default_skill:
            self.set_spell(default_skill)
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return [
            PassiveSkill.ARMOR_BLESSING,
            PassiveSkill.DOUBLE_HEAL,
            PassiveSkill.EMPOWERED_HEAL,
            PassiveSkill.HOLY_SMITE,
            PassiveSkill.BATTLE_HEAL,
            PassiveSkill.MASS_HEAL,
            PassiveSkill.CLEANSE
        ]
    
    def get_passive_skill_cost(self, skill_name) -> int:
        """Get the cost of a passive skill"""
        costs = {
            PassiveSkill.ARMOR_BLESSING: 35,
            PassiveSkill.DOUBLE_HEAL: 40,
            PassiveSkill.EMPOWERED_HEAL: 30,
            PassiveSkill.HOLY_SMITE: 45,
            PassiveSkill.BATTLE_HEAL: 25,
            PassiveSkill.MASS_HEAL: 50,
            PassiveSkill.CLEANSE: 35,
        }
        return costs.get(skill_name, 30)
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 45

def create_cleric() -> Cleric:
    """Factory function to create a cleric"""
    return Cleric()


# ===== CLERIC SKILLS =====

class Heal(Skill):
    def __init__(self):
        super().__init__("Heal", "Heal the lowest HP ally for 400")
        self.cast_time = 1.5
        self.mana_cost = 60
        self.heal_amount = 400
        self.cast_count = 0  # Track cast count for Mass Heal passive
        
    def should_cast(self, caster) -> bool:
        # Cast if there are injured allies
        if not caster.board:
            return False
        allies = caster.board.get_allied_units(caster.team)
        for ally in allies:
            if ally.is_alive() and ally.hp < ally.max_hp:
                return True
        return False
        
    def execute(self, caster):
        if not caster.board:
            return
            
        # Mass Heal passive - every 4th cast heals all allies
        if self._caster_has_passive_skill(caster, PassiveSkill.MASS_HEAL):
            self.cast_count += 1
            if self.cast_count >= 4:
                self.cast_count = 0
                # Heal all allies
                allies = caster.board.get_allied_units(caster.team)
                for ally in allies:
                    if ally.is_alive() and ally.hp < ally.max_hp:
                        heal_amount = self.heal_amount
                        # Apply Empowered Heal bonus if target is below 50% HP
                        if self._caster_has_passive_skill(caster, PassiveSkill.EMPOWERED_HEAL) and ally.hp < ally.max_hp * 0.5:
                            heal_amount = int(heal_amount * 1.5)
                        ally.heal(heal_amount, caster)
                        self._apply_cleric_effects(caster, ally)
                        if caster.board:
                            from visual_effect import VisualEffectType
                            caster.board.add_visual_effect(VisualEffectType.HOLY, ally.x, ally.y)
                return
        
        # Find lowest HP ally (by percentage)
        allies = caster.board.get_allied_units(caster.team)
        injured_allies = [ally for ally in allies if ally.is_alive() and ally.hp < ally.max_hp]
        
        if not injured_allies:
            return
            
        # Find ally with lowest HP percentage
        target = min(injured_allies, key=lambda a: a.hp / a.max_hp)
        
        # Calculate heal amount
        heal_amount = self.heal_amount
        
        # Empowered Heal passive - heal for 50% more if target below 50% HP
        if self._caster_has_passive_skill(caster, PassiveSkill.EMPOWERED_HEAL) and target.hp < target.max_hp * 0.5:
            heal_amount = int(heal_amount * 1.5)
        
        # Heal the target
        target.heal(heal_amount, caster)
        
        # Apply other passive effects
        self._apply_cleric_effects(caster, target)
        
        # Double Heal passive - also heal 2nd lowest HP ally for 200
        if self._caster_has_passive_skill(caster, PassiveSkill.DOUBLE_HEAL):
            remaining_allies = [ally for ally in injured_allies if ally != target]
            if remaining_allies:
                second_target = min(remaining_allies, key=lambda a: a.hp / a.max_hp)
                second_heal = 200
                if self._caster_has_passive_skill(caster, PassiveSkill.EMPOWERED_HEAL) and second_target.hp < second_target.max_hp * 0.5:
                    second_heal = int(second_heal * 1.5)
                second_target.heal(second_heal, caster)
                self._apply_cleric_effects(caster, second_target)
                if caster.board:
                    from visual_effect import VisualEffectType
                    caster.board.add_visual_effect(VisualEffectType.HOLY, second_target.x, second_target.y)
        
        # Visual effect
        if caster.board:
            from visual_effect import VisualEffectType
            caster.board.add_visual_effect(VisualEffectType.HOLY, target.x, target.y)
    
    def _apply_cleric_effects(self, caster, target):
        """Apply passive effects to healed target"""
        # Armor Blessing - target gains 50 armor and 50 MR until end of combat
        if self._caster_has_passive_skill(caster, PassiveSkill.ARMOR_BLESSING):
            has_blessing = any(e.name == "Armor Blessing" for e in target.status_effects)
            if not has_blessing:
                from status_effect import StatModifierEffect
                effect = StatModifierEffect("Armor Blessing", None, {"armor": 50, "magic_resist": 50})
                effect.source = caster
                target.add_status_effect(effect)
        
        # Cleanse - remove all debuffs
        if self._caster_has_passive_skill(caster, PassiveSkill.CLEANSE):
            debuffs_to_remove = []
            for effect in target.status_effects:
                # Remove negative effects (this is a simplified check)
                if hasattr(effect, 'is_debuff') and effect.is_debuff:
                    debuffs_to_remove.append(effect)
            for debuff in debuffs_to_remove:
                target.remove_status_effect(debuff)
        
        # Holy Smite - deal holy damage to nearest enemy
        if self._caster_has_passive_skill(caster, PassiveSkill.HOLY_SMITE):
            enemies = caster.board.get_enemy_units(caster.team)
            living_enemies = [enemy for enemy in enemies if enemy.is_alive()]
            if living_enemies:
                nearest_enemy = min(living_enemies, key=lambda e: caster.board.distance(target.x, target.y, e.x, e.y))
                nearest_enemy.take_damage(200, "holy", caster)
                if caster.board:
                    from visual_effect import VisualEffectType
                    caster.board.add_visual_effect(VisualEffectType.HOLY, nearest_enemy.x, nearest_enemy.y)
    
    def _caster_has_passive_skill(self, caster, skill_enum: PassiveSkill) -> bool:
        """Check if caster has a specific passive skill"""
        for passive in caster.passive_skills:
            if hasattr(passive, 'skill_enum') and passive.skill_enum == skill_enum:
                return True
        return False


class ArmorBlessing(Skill):
    """Healed ally gains armor and magic resist until end of combat"""
    def __init__(self):
        super().__init__("Armor Blessing", "Healed ally gains 50 armor and 50 MR until end of combat")
        self.is_passive = True
        self.skill_enum = PassiveSkill.ARMOR_BLESSING
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class DoubleHeal(Skill):
    """Also heal the 2nd lowest hp ally for 200"""
    def __init__(self):
        super().__init__("Double Heal", "Also heal the 2nd lowest hp ally for 200")
        self.is_passive = True
        self.skill_enum = PassiveSkill.DOUBLE_HEAL
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class EmpoweredHeal(Skill):
    """Heal for 50% more if target is below 50% hp"""
    def __init__(self):
        super().__init__("Empowered Heal", "If the ally is below 50% hp heal for 50% more")
        self.is_passive = True
        self.skill_enum = PassiveSkill.EMPOWERED_HEAL
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class HolySmite(Skill):
    """Deal holy damage to nearest enemy to the healed unit"""
    def __init__(self):
        super().__init__("Holy Smite", "Deal 200 holy damage to the nearest enemy to the healed unit")
        self.is_passive = True
        self.skill_enum = PassiveSkill.HOLY_SMITE
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class BattleHeal(Skill):
    """On hitting an enemy, heal nearest ally for 50 hp"""
    def __init__(self):
        super().__init__("Battle Heal", "On hitting an enemy, heal nearest ally (break ties randomly) for 50 hp")
        self.is_passive = True
        self.skill_enum = PassiveSkill.BATTLE_HEAL
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and "attacker" in kwargs and "target" in kwargs and "damage" in kwargs:
            attacker = kwargs["attacker"]
            target = kwargs["target"]
            damage = kwargs["damage"]
            
            if attacker == self.owner and damage > 0 and target.team != attacker.team:
                # Find nearest ally to heal
                allies = attacker.board.get_allied_units(attacker.team)
                injured_allies = [ally for ally in allies if ally.is_alive() and ally.hp < ally.max_hp]
                
                if injured_allies:
                    # Find nearest ally (break ties randomly)
                    import random
                    nearest_distance = min(attacker.board.distance(attacker.x, attacker.y, ally.x, ally.y) for ally in injured_allies)
                    nearest_allies = [ally for ally in injured_allies if attacker.board.distance(attacker.x, attacker.y, ally.x, ally.y) == nearest_distance]
                    target_ally = random.choice(nearest_allies)
                    target_ally.heal(50, attacker)
                    
                    if attacker.board:
                        from visual_effect import VisualEffectType
                        attacker.board.add_visual_effect(VisualEffectType.HOLY, target_ally.x, target_ally.y)


class MassHeal(Skill):
    """Every 4th cast heals ALL allies instead of just one"""
    def __init__(self):
        super().__init__("Mass Heal", "Every 4th cast heals ALL allies instead of just one")
        self.is_passive = True
        self.skill_enum = PassiveSkill.MASS_HEAL
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class Cleanse(Skill):
    """The target is cleansed of all debuffs"""
    def __init__(self):
        super().__init__("Cleanse", "The target is cleansed of all debuffs (poison etc)")
        self.is_passive = True
        self.skill_enum = PassiveSkill.CLEANSE
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


def create_cleric_skill(skill_name) -> Skill:
    """Create cleric-specific skills"""
    skill_classes = {
        "heal": Heal,
        PassiveSkill.ARMOR_BLESSING: ArmorBlessing,
        PassiveSkill.DOUBLE_HEAL: DoubleHeal,
        PassiveSkill.EMPOWERED_HEAL: EmpoweredHeal,
        PassiveSkill.HOLY_SMITE: HolySmite,
        PassiveSkill.BATTLE_HEAL: BattleHeal,
        PassiveSkill.MASS_HEAL: MassHeal,
        PassiveSkill.CLEANSE: Cleanse,
    }
    
    # Handle both string and enum inputs for backwards compatibility
    if isinstance(skill_name, str):
        skill_class = skill_classes.get(skill_name.lower())
    else:
        skill_class = skill_classes.get(skill_name)
        
    if skill_class:
        return skill_class()
    return None