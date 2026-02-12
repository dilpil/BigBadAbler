import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unit import Unit, UnitType
from skill import Skill

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
        self.set_spell(HolyAura())
    
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
        if not caster.board:
            return False
        allies = caster.board.get_units_in_range(caster.x, caster.y, self.range, caster.team)
        for ally in allies:
            if ally.is_alive() and ally.hp < ally.max_hp:
                return True
        return False
        
    def execute(self, caster):
        # Heal allies
        if not caster.board:
            return
        allies = caster.board.get_units_in_range(caster.x, caster.y, self.range, caster.team)
        for ally in allies:
            if ally.is_alive():
                ally.heal(self.heal_amount, caster)
                # Add visual effect at healed ally's position
                if caster.board:
                    from visual_effect import VisualEffectType
                    caster.board.add_visual_effect(VisualEffectType.HOLY, ally.x, ally.y)
