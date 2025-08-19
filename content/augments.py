import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from augment import Augment, UnitAugment, ItemAugment, PassiveAugment
from content.items import create_item
import random


# Passive Augments

class AttackBoostAugment(PassiveAugment):
    """Increases attack damage of all units by 25%"""
    
    def __init__(self):
        super().__init__(
            "Berserker's Blessing",
            "All your units gain +25% attack damage",
            40
        )
        
    def on_battle_start(self):
        """Apply the attack boost to all units at battle start"""
        if self.game and self.game.board:
            for unit in self.game.board.player_units:
                if unit.is_alive():
                    unit.attack_damage = int(unit.attack_damage * 1.25)


class HealthBoostAugment(PassiveAugment):
    """Increases max HP of all units by 25%"""
    
    def __init__(self):
        super().__init__(
            "Vitality Surge",
            "All your units gain +25% max HP",
            40
        )
        
    def on_battle_start(self):
        """Apply the HP boost to all units at battle start"""
        if self.game and self.game.board:
            for unit in self.game.board.player_units:
                if unit.is_alive():
                    hp_increase = int(unit.max_hp * 0.25)
                    unit.max_hp += hp_increase
                    unit.hp += hp_increase  # Also heal for the increased amount


class ArmorBoostAugment(PassiveAugment):
    """Increases armor of all units by 25"""
    
    def __init__(self):
        super().__init__(
            "Iron Fortification",
            "All your units gain +25 armor",
            35
        )
        
    def on_battle_start(self):
        """Apply the armor boost to all units at battle start"""
        if self.game and self.game.board:
            for unit in self.game.board.player_units:
                if unit.is_alive():
                    unit.armor += 25


class AttackSpeedBoostAugment(PassiveAugment):
    """Increases attack speed of all units by 25%"""
    
    def __init__(self):
        super().__init__(
            "Swift Strikes",
            "All your units gain +25% attack speed",
            40
        )
        
    def on_battle_start(self):
        """Apply the attack speed boost to all units at battle start"""
        if self.game and self.game.board:
            for unit in self.game.board.player_units:
                if unit.is_alive():
                    unit.attack_speed += 25


class GoldGenerationAugment(PassiveAugment):
    """Generates extra gold each round"""
    
    def __init__(self):
        super().__init__(
            "Merchant's Fortune",
            "Gain +10 gold at the end of each round",
            30
        )
        
    def on_round_end(self):
        """Add extra gold at the end of the round"""
        if self.game:
            self.game.gold += 10


# Item Augments - wrap existing items

class FrenzyMaskAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Frenzy Mask",
            "Item: On attack +5% AS, +10 armor",
            45,
            lambda: create_item("frenzy_mask")
        )


class ThrumbladeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Thrumblade",
            "Item: Every second +5 AD, +10% max HP",
            50,
            lambda: create_item("thrumblade")
        )


class HammerOfBamAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Hammer of Bam",
            "Item: Every 3rd attack deals 300% damage",
            55,
            lambda: create_item("hammer_of_bam")
        )


class ManastaffAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Manastaff",
            "Item: +5 MP/s, on cast projectile deals mana cost",
            60,
            lambda: create_item("manastaff")
        )


class BurnmailAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Burnmail",
            "Item: +50 armor +25 MR, burn nearby enemies",
            70,
            lambda: create_item("burnmail")
        )


class ScorpionTailAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Scorpion Tail",
            "Item: +10 AD, attacks inflict poison",
            40,
            lambda: create_item("scorpion_tail")
        )


class PhylacteryAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Phylactery",
            "Item: At 50% HP cleanse and heal to full",
            80,
            lambda: create_item("phylactery")
        )


class SundererAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Sunderer",
            "Item: +20 AD, attacks apply -5 armor",
            45,
            lambda: create_item("sunderer")
        )


class BeastheartAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Beastheart",
            "Item: +500 HP, +25% max HP",
            65,
            lambda: create_item("beastheart")
        )


class PhantomSaberAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Phantom Saber",
            "Item: +10 all stats, spawns 2 clones",
            90,
            lambda: create_item("phantom_saber")
        )


class SnowGlobeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Snow Globe",
            "Item: +20 int, magic damage applies chill",
            50,
            lambda: create_item("snow_globe")
        )


class EchostoneAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Echostone",
            "Item: Cast abilities twice at 50% int",
            75,
            lambda: create_item("echostone")
        )


class OminstoneAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Ominstone",
            "Item: +20 all combat stats",
            100,
            lambda: create_item("ominstone")
        )


class RedWavebladeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Red Waveblade",
            "Item: +30 AD, +30% attack speed",
            55,
            lambda: create_item("red_waveblade")
        )


class BlueWavebladeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Blue Waveblade",
            "Item: +30 int, +30% attack speed",
            55,
            lambda: create_item("blue_waveblade")
        )


class NegationHelmAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Negation Helm",
            "Item: +60 MR, +4 MP/s",
            60,
            lambda: create_item("negation_helm")
        )


class ArmorOfTimeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Armor of Time",
            "Item: +10 armor/MR, +2 per second",
            65,
            lambda: create_item("armor_of_time")
        )


# Rare Unit Augments

class DragonAugment(UnitAugment):
    def __init__(self):
        def create_dragon():
            from content.units.dragon import Dragon
            return Dragon()
        
        super().__init__(
            "Ancient Dragon",
            "Rare Unit: Dragon with 3000 HP and fire breath",
            150,
            create_dragon
        )


# Factory function to get all augments
def get_all_augment_types():
    """Returns a list of all augment class constructors"""
    return [
        # Passive augments
        AttackBoostAugment,
        HealthBoostAugment,
        ArmorBoostAugment,
        AttackSpeedBoostAugment,
        GoldGenerationAugment,
        
        # Item augments
        FrenzyMaskAugment,
        ThrumbladeAugment,
        HammerOfBamAugment,
        ManastaffAugment,
        BurnmailAugment,
        ScorpionTailAugment,
        PhylacteryAugment,
        SundererAugment,
        BeastheartAugment,
        PhantomSaberAugment,
        SnowGlobeAugment,
        EchostoneAugment,
        OminstoneAugment,
        RedWavebladeAugment,
        BlueWavebladeAugment,
        NegationHelmAugment,
        ArmorOfTimeAugment,
        
        # Rare unit augments
        DragonAugment
    ]


def generate_augment_shop(count: int = 10) -> list:
    """Generate a random shop of augments"""
    all_augment_types = get_all_augment_types()
    
    # Weight different augment types
    weights = []
    for augment_type in all_augment_types:
        if issubclass(augment_type, PassiveAugment):
            weights.append(3)  # Common
        elif issubclass(augment_type, ItemAugment):
            weights.append(2)  # Less common
        elif issubclass(augment_type, UnitAugment):
            weights.append(1)  # Rare
        else:
            weights.append(2)  # Default
    
    # Select random augments
    selected_types = random.choices(all_augment_types, weights=weights, k=count)
    return [augment_type() for augment_type in selected_types]