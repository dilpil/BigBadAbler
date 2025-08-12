import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill
from status_effect import StatModifierEffect

class Paladin(Unit):
    def __init__(self):
        super().__init__("Paladin", UnitType.PALADIN)
        self.max_hp = 850
        self.hp = self.max_hp
        self.max_mp = 60
        self.mp = 0
        self.attack_damage = 60
        self.attack_range = 1
        self.attack_speed = -30  # 0.7 attacks per second
        self.strength = 15
        self.armor = 45
        self.magic_resist = 45
        
        # Set default skill immediately upon creation
        self._set_default_skill()
    
    def _set_default_skill(self):
        """Set the default skill for this unit"""
        default_skill = create_paladin_skill("holy_heal")
        if default_skill:
            self.set_spell(default_skill)
    
    def get_available_passive_skills(self) -> list:
        """Get list of available passive skills for this unit"""
        return [
            "smite",
            "protection",
            "lay_hands_on",
            "holy_thunder",
            "healing_aura"
        ]
    
    def get_passive_skill_cost(self, skill_name: str) -> int:
        """Get the cost of a passive skill"""
        costs = {
            "smite": 40,
            "protection": 45,
            "lay_hands_on": 35,
            "holy_thunder": 30,
            "healing_aura": 35,
        }
        return costs.get(skill_name, 30)
    
    @staticmethod
    def get_cost() -> int:
        """Get the gold cost to purchase this unit"""
        return 50

def create_paladin() -> Paladin:
    """Factory function to create a paladin"""
    return Paladin()


# ===== PALADIN SKILLS =====

class HolyAura(Skill):
    def __init__(self):
        super().__init__("Holy Heal", "Heals all allies within 4 tiles for 250 HP")
        self.cast_time = 0.25
        self.mana_cost = 60
        self.heal_amount = 250
        self.range = 4
        
    def should_cast(self, caster) -> bool:
        # Cast if there are injured allies in range
        allies = caster.board.get_units_in_range(caster.x, caster.y, self.range, caster.team)
        for ally in allies:
            if ally.is_alive() and ally.hp < ally.max_hp:
                return True
        return False
        
    def execute(self, caster):
        # Heal allies
        allies = caster.board.get_units_in_range(caster.x, caster.y, self.range, caster.team)
        for ally in allies:
            if ally.is_alive():
                ally.heal(self.heal_amount, caster)
                # Add visual effect at healed ally's position
                if caster.board:
                    from visual_effect import VisualEffectType
                    caster.board.add_visual_effect(VisualEffectType.HOLY, ally.x, ally.y)
        
        # Smite passive - damage enemies in range
        if self._caster_has_passive_skill(caster, "smite"):
            enemies = caster.board.get_units_in_range(caster.x, caster.y, self.range, "enemy" if caster.team == "player" else "player")
            for enemy in enemies:
                if enemy.is_alive():
                    enemy.take_damage(200, "magical", caster)
                    if caster.board:
                        caster.board.add_visual_effect(VisualEffectType.HOLY, enemy.x, enemy.y)
        
        # Lay Hands On passive - extra heal to most wounded adjacent ally
        if self._caster_has_passive_skill(caster, "lay_hands_on"):
            adjacent_allies = caster.board.get_units_in_range(caster.x, caster.y, 1, caster.team)
            adjacent_allies = [ally for ally in adjacent_allies if ally.is_alive() and ally != caster and ally.hp < ally.max_hp]
            if adjacent_allies:
                # Find most wounded (lowest HP percentage)
                most_wounded = min(adjacent_allies, key=lambda a: a.hp / a.max_hp)
                most_wounded.heal(400, caster)
                if caster.board:
                    caster.board.add_visual_effect(VisualEffectType.HOLY, most_wounded.x, most_wounded.y)
    
    def _caster_has_passive_skill(self, caster, skill_name: str) -> bool:
        """Check if caster has a specific passive skill"""
        for passive in caster.passive_skills:
            if passive.name.lower().replace(" ", "_") == skill_name.lower():
                return True
        return False


class Smite(Skill):
    """Holy Heal also damages enemies in range"""
    def __init__(self):
        super().__init__("Smite", "Holy Heal also deals 200 magical damage to enemies in range")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class Protection(Skill):
    """Paladin provides armor and magic resist aura to nearby allies"""
    def __init__(self):
        super().__init__("Protection", "Provides +50 armor and +50 magic resist to allies within 4 tiles")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.range = 4
        self.armor_bonus = 50
        self.mr_bonus = 50
        
    def update(self, dt: float):
        super().update(dt)
        if not self.owner or not self.owner.is_alive():
            return
            
        # Apply protection buff to nearby allies
        allies = self.owner.board.get_units_in_range(self.owner.x, self.owner.y, self.range, self.owner.team)
        for ally in allies:
            if ally.is_alive():
                # Check if ally already has protection buff
                has_protection = any(e.name == "Protection" for e in ally.status_effects)
                if not has_protection:
                    effect = StatModifierEffect("Protection", 2.0, {"armor": self.armor_bonus, "magic_resist": self.mr_bonus})
                    effect.source = self.owner
                    ally.add_status_effect(effect)


class LayHandsOn(Skill):
    """Extra healing for most wounded adjacent ally"""
    def __init__(self):
        super().__init__("Lay Hands On", "On cast, heals the most wounded adjacent ally for an additional 400 HP")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0


class HolyThunder(Skill):
    """Melee attacks deal bonus lightning damage"""
    def __init__(self):
        super().__init__("Holy Thunder", "Melee attacks deal an additional 65 lightning damage")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.bonus_damage = 65
        
    def on_event(self, event_type: str, **kwargs):
        if event_type == "unit_attack" and "attacker" in kwargs and "target" in kwargs:
            attacker = kwargs["attacker"]
            target = kwargs["target"]
            if attacker == self.owner and attacker.attack_range == 1:  # Melee attack
                target.take_damage(self.bonus_damage, "lightning", attacker)


class HealingAura(Skill):
    """Passive healing aura for nearby allies"""
    def __init__(self):
        super().__init__("Healing Aura", "Passively heals all allies within 4 tiles for 20 HP every 0.5 seconds")
        self.is_passive = True
        self.cast_time = None
        self.mana_cost = 0
        self.current_mana = 0
        self.heal_amount = 20
        self.range = 4
        self.tick_timer = 0
        self.tick_interval = 0.5
        
    def update(self, dt: float):
        super().update(dt)
        if not self.owner or not self.owner.is_alive():
            return
            
        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            allies = self.owner.board.get_units_in_range(self.owner.x, self.owner.y, self.range, self.owner.team)
            for ally in allies:
                if ally.is_alive():
                    ally.heal(self.heal_amount, self.owner)


def create_paladin_skill(skill_name: str) -> Skill:
    """Create paladin-specific skills"""
    skill_classes = {
        "holy_heal": HolyAura,
        "smite": Smite,
        "protection": Protection,
        "lay_hands_on": LayHandsOn,
        "holy_thunder": HolyThunder,
        "healing_aura": HealingAura,
    }
    
    skill_class = skill_classes.get(skill_name.lower())
    if skill_class:
        return skill_class()
    return None