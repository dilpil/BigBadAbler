import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from augment import Augment, UnitAugment, ItemAugment, PassiveAugment
from content.items import create_item
from unit import UnitType
from status_effect import StatModifierEffect
import random


# Shop Entry Types (not augments - these are shop slots for characters)

class CharacterShopEntry:
    """A character available for purchase in the shop."""

    def __init__(self, unit_type: UnitType, team=None):
        self.unit_type = unit_type
        self.team = team  # Reference to player team for dynamic cost
        self.name = unit_type.name.replace("_", " ").title()
        self.description = f"Purchase a {self.name}"

    @property
    def cost(self):
        """Calculate cost dynamically based on current unit count."""
        if self.team:
            return self.team.get_unit_cost()
        return 40  # Base cost if no team

    def get_tooltip(self):
        return f"{self.name}\nCost: {self.cost}\nCharacter"


# Passive Augments

class AttackBoostAugment(PassiveAugment):
    """Increases attack damage of all units by 25%"""

    def __init__(self):
        super().__init__(
            "Berserker's Blessing",
            "All your units gain +25% attack damage",
            40
        )

    def apply_to_unit(self, unit):
        """Apply attack boost to a single unit"""
        if unit.is_alive():
            bonus = int(unit.attack_damage * 0.25)
            effect = StatModifierEffect(
                "Berserker's Blessing",
                duration=None,
                stat_changes={"attack_damage": bonus}
            )
            effect.source = self
            unit.add_status_effect(effect)

    def on_buy(self, team):
        """When purchased, apply to all existing units"""
        super().on_buy(team)
        for unit in team.units:
            self.apply_to_unit(unit)
        return True


class HealthBoostAugment(PassiveAugment):
    """Increases max HP of all units by 25%"""

    def __init__(self):
        super().__init__(
            "Vitality Surge",
            "All your units gain +25% max HP",
            40
        )

    def apply_to_unit(self, unit):
        """Apply HP boost to a single unit"""
        if unit.is_alive():
            # Check if unit already has this effect to avoid double-applying hp bonus
            has_effect = any(e.name == "Vitality Surge" for e in unit.status_effects)
            if has_effect:
                return

            hp_bonus = int(unit.max_hp * 0.25)
            effect = StatModifierEffect(
                "Vitality Surge",
                duration=None,
                stat_changes={"max_hp": hp_bonus}
            )
            effect.source = self
            unit.add_status_effect(effect)
            # Also increase current hp to match the new max
            unit.hp = min(unit.hp + hp_bonus, unit.max_hp)

    def on_buy(self, team):
        """When purchased, apply to all existing units"""
        super().on_buy(team)
        for unit in team.units:
            self.apply_to_unit(unit)
        return True


class ArmorBoostAugment(PassiveAugment):
    """Increases armor of all units by 25"""

    def __init__(self):
        super().__init__(
            "Iron Fortification",
            "All your units gain +25 armor",
            35
        )

    def apply_to_unit(self, unit):
        """Apply armor boost to a single unit"""
        if unit.is_alive():
            effect = StatModifierEffect(
                "Iron Fortification",
                duration=None,
                stat_changes={"armor": 25}
            )
            effect.source = self
            unit.add_status_effect(effect)

    def on_buy(self, team):
        """When purchased, apply to all existing units"""
        super().on_buy(team)
        for unit in team.units:
            self.apply_to_unit(unit)
        return True


class AttackSpeedBoostAugment(PassiveAugment):
    """Increases attack speed of all units by 25%"""

    def __init__(self):
        super().__init__(
            "Swift Strikes",
            "All your units gain +25% attack speed",
            40
        )

    def apply_to_unit(self, unit):
        """Apply attack speed boost to a single unit"""
        if unit.is_alive():
            bonus = int(unit.attack_speed * 0.25)
            # Minimum bonus of 25 if unit has low attack speed
            bonus = max(bonus, 25)
            effect = StatModifierEffect(
                "Swift Strikes",
                duration=None,
                stat_changes={"attack_speed": bonus}
            )
            effect.source = self
            unit.add_status_effect(effect)

    def on_buy(self, team):
        """When purchased, apply to all existing units"""
        super().on_buy(team)
        for unit in team.units:
            self.apply_to_unit(unit)
        return True


# New Global Augments (converted from unit upgrades)

class DefensiveAuraAugment(PassiveAugment):
    """All allies gain armor and magic resist"""

    def __init__(self):
        super().__init__(
            "Defensive Aura",
            "All your units gain +50 armor and +50 magic resist",
            50
        )

    def apply_to_unit(self, unit):
        """Apply defensive aura to a single unit"""
        if unit.is_alive():
            effect = StatModifierEffect(
                "Defensive Aura",
                duration=None,
                stat_changes={"armor": 50, "magic_resist": 50}
            )
            effect.source = self
            unit.add_status_effect(effect)

    def on_buy(self, team):
        """When purchased, apply to all existing units"""
        super().on_buy(team)
        for unit in team.units:
            self.apply_to_unit(unit)
        return True


class RegenerationFieldAugment(PassiveAugment):
    """All allies passively heal over time"""

    def __init__(self):
        super().__init__(
            "Regeneration Field",
            "All your units heal 20 HP every 0.5 seconds",
            45
        )
        self.tick_timer = 0
        self.tick_interval = 0.5
        self.heal_amount = 20

    def on_frame(self, dt: float):
        if not self.team or not self.team.board:
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            for unit in self.team.units:
                if unit.is_alive():
                    unit.heal(self.heal_amount, None)


class FireResistanceAugment(PassiveAugment):
    """All allies gain fire resistance"""

    def __init__(self):
        super().__init__(
            "Fire Resistance",
            "All your units gain +50 fire resistance",
            35
        )

    def apply_to_unit(self, unit):
        """Apply fire resistance to a single unit"""
        if unit.is_alive():
            effect = StatModifierEffect(
                "Fire Resistance",
                duration=None,
                stat_changes={"fire_resist": 50}
            )
            effect.source = self
            unit.add_status_effect(effect)

    def on_buy(self, team):
        """When purchased, apply to all existing units"""
        super().on_buy(team)
        for unit in team.units:
            self.apply_to_unit(unit)
        return True


class DeathsChillAugment(PassiveAugment):
    """Enemy deaths deal ice damage to nearby enemies"""

    def __init__(self):
        super().__init__(
            "Death's Chill",
            "When an enemy dies, deal 10% of their max HP as ice damage to a random nearby enemy",
            40
        )

    def on_event(self, event_type: str, **kwargs):
        if event_type == "death" and "dying_unit" in kwargs:
            dying_unit = kwargs["dying_unit"]
            # Only trigger for enemy units
            if self.team and dying_unit.team != self.team.name:
                self.apply_chill(dying_unit)

    def apply_chill(self, dying_unit):
        import random
        if not self.team or not self.team.board:
            return

        # Find enemies near the dying unit
        enemy_team = "enemy" if self.team.name == "player" else "player"
        nearby_enemies = self.team.board.get_units_in_range(dying_unit.x, dying_unit.y, 3, enemy_team)
        nearby_enemies = [e for e in nearby_enemies if e != dying_unit and e.is_alive()]

        if nearby_enemies:
            target = random.choice(nearby_enemies)
            damage = dying_unit.max_hp * 0.10
            target.take_damage(damage, "magical", None)


class PurificationAugment(PassiveAugment):
    """Allies are cleansed of debuffs when healed"""

    def __init__(self):
        super().__init__(
            "Purification",
            "When any of your units is healed, cleanse all debuffs from them",
            40
        )

    def on_event(self, event_type: str, **kwargs):
        if event_type == "heal" and "target" in kwargs:
            target = kwargs["target"]
            if self.team and target.team == self.team.name:
                self.cleanse_debuffs(target)

    def cleanse_debuffs(self, unit):
        debuffs_to_remove = []
        for effect in unit.status_effects:
            if hasattr(effect, 'is_debuff') and effect.is_debuff:
                debuffs_to_remove.append(effect)
        for debuff in debuffs_to_remove:
            unit.remove_status_effect(debuff)


class SoulHarvestAugment(PassiveAugment):
    """Units heal when adjacent enemies die"""

    def __init__(self):
        super().__init__(
            "Soul Harvest",
            "Your units heal 400 HP when an adjacent enemy dies",
            45
        )

    def on_event(self, event_type: str, **kwargs):
        if event_type == "death" and "dying_unit" in kwargs:
            dying_unit = kwargs["dying_unit"]
            # Only trigger for enemy deaths
            if self.team and dying_unit.team != self.team.name:
                self.heal_nearby_allies(dying_unit)

    def heal_nearby_allies(self, dying_unit):
        if not self.team or not self.team.board:
            return

        for unit in self.team.units:
            if unit.is_alive():
                distance = self.team.board.get_distance(unit, dying_unit)
                if distance <= 1:
                    unit.heal(400, None)


# ===== NEW PASSIVE AUGMENTS =====

class FlatHealthAugment(PassiveAugment):
    """All units get +250 HP"""

    def __init__(self):
        super().__init__(
            "Fortitude",
            "All your units gain +250 max HP",
            35
        )

    def apply_to_unit(self, unit):
        if unit.is_alive():
            has_effect = any(e.name == "Fortitude" for e in unit.status_effects)
            if has_effect:
                return
            effect = StatModifierEffect(
                "Fortitude",
                duration=None,
                stat_changes={"max_hp": 250}
            )
            effect.source = self
            unit.add_status_effect(effect)
            unit.hp = min(unit.hp + 250, unit.max_hp)

    def on_buy(self, team):
        super().on_buy(team)
        for unit in team.units:
            self.apply_to_unit(unit)
        return True


class KnightSynergyAugment(PassiveAugment):
    """All units get +10 armor and +10 MR for each Magic Knight you control"""

    def __init__(self):
        super().__init__(
            "Knight's Order",
            "All units gain +10 armor and +10 MR for each Magic Knight you control",
            45
        )

    def on_battle_start(self):
        if not self.team:
            return
        # Count magic knights
        knight_count = sum(1 for u in self.team.units if u.unit_type.value == "magic_knight")
        if knight_count == 0:
            return

        bonus = knight_count * 10
        for unit in self.team.units:
            if unit.is_alive():
                effect = StatModifierEffect(
                    "Knight's Order",
                    duration=None,
                    stat_changes={"armor": bonus, "magic_resist": bonus}
                )
                effect.source = self
                unit.add_status_effect(effect)


class WizardSynergyAugment(PassiveAugment):
    """All units get +1 MP/s for each Wizard you control"""

    def __init__(self):
        super().__init__(
            "Arcane Resonance",
            "All units gain +1 MP/s for each Wizard you control",
            40
        )

    def on_battle_start(self):
        if not self.team:
            return
        # Count wizards
        wizard_count = sum(1 for u in self.team.units if u.unit_type.value == "wizard")
        if wizard_count == 0:
            return

        bonus = wizard_count
        for unit in self.team.units:
            if unit.is_alive():
                unit.mp_regen += bonus


class FormationAugment(PassiveAugment):
    """Front row units get +50% HP, back row units get +50% intelligence"""

    def __init__(self):
        super().__init__(
            "Battle Formation",
            "Front row (x<2) units get +50% HP, back row (x>=2) units get +50% intelligence",
            50
        )

    def on_battle_start(self):
        if not self.team:
            return

        for unit in self.team.units:
            if not unit.is_alive():
                continue

            if unit.x < 2:  # Front row
                hp_bonus = int(unit.max_hp * 0.5)
                effect = StatModifierEffect(
                    "Front Line",
                    duration=None,
                    stat_changes={"max_hp": hp_bonus}
                )
                effect.source = self
                unit.add_status_effect(effect)
                unit.hp = min(unit.hp + hp_bonus, unit.max_hp)
            else:  # Back row
                int_bonus = int(unit.intelligence * 0.5)
                if int_bonus < 15:
                    int_bonus = 15  # Minimum bonus
                effect = StatModifierEffect(
                    "Back Line",
                    duration=None,
                    stat_changes={"intelligence": int_bonus}
                )
                effect.source = self
                unit.add_status_effect(effect)


class ScalingDamageAugment(PassiveAugment):
    """Each second, all units gain +1 attack damage"""

    def __init__(self):
        super().__init__(
            "Growing Power",
            "Each second, all your units gain +1 attack damage",
            40
        )
        self.tick_timer = 0
        self.tick_interval = 1.0

    def on_frame(self, dt: float):
        if not self.team:
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            for unit in self.team.units:
                if unit.is_alive():
                    unit.attack_damage += 1


class ScalingDefenseAugment(PassiveAugment):
    """Each second, all units gain +1 armor and +1 magic resist"""

    def __init__(self):
        super().__init__(
            "Hardening",
            "Each second, all your units gain +1 armor and +1 magic resist",
            40
        )
        self.tick_timer = 0
        self.tick_interval = 1.0

    def on_frame(self, dt: float):
        if not self.team:
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            for unit in self.team.units:
                if unit.is_alive():
                    unit.armor += 1
                    unit.magic_resist += 1


class GlobalRegenAugment(PassiveAugment):
    """All units heal for 1% of max HP per second"""

    def __init__(self):
        super().__init__(
            "Life Force",
            "All your units heal for 1% of their max HP every second",
            45
        )
        self.tick_timer = 0
        self.tick_interval = 1.0

    def on_frame(self, dt: float):
        if not self.team:
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            for unit in self.team.units:
                if unit.is_alive():
                    heal_amount = unit.max_hp * 0.01
                    unit.heal(heal_amount, None)


class LowestHPHealAugment(PassiveAugment):
    """Lowest HP unit heals for 3% of max HP per second"""

    def __init__(self):
        super().__init__(
            "Guardian Angel",
            "Your lowest HP unit heals for 3% of their max HP every second",
            40
        )
        self.tick_timer = 0
        self.tick_interval = 1.0

    def on_frame(self, dt: float):
        if not self.team:
            return

        self.tick_timer += dt
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            # Find lowest HP unit (by percentage)
            living_units = [u for u in self.team.units if u.is_alive()]
            if living_units:
                lowest = min(living_units, key=lambda u: u.hp / u.max_hp)
                heal_amount = lowest.max_hp * 0.03
                lowest.heal(heal_amount, None)


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


# New Item Augments (converted from unit upgrades)

class ThunderGlovesAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Thunder Gloves",
            "Item: +65 lightning damage on melee attacks",
            45,
            lambda: create_item("thunder_gloves")
        )


class LeapBootsAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Leap Boots",
            "Item: On kill, leap to lowest HP enemy",
            50,
            lambda: create_item("leap_boots")
        )


class ArmorShredderAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Armor Shredder",
            "Item: Attacks reduce target armor by 1",
            40,
            lambda: create_item("armor_shredder")
        )


class CleavingBladeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Cleaving Blade",
            "Item: Attacks hit 3 adjacent enemies",
            55,
            lambda: create_item("cleaving_blade")
        )


class FireStaffAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Fire Staff",
            "Item: Attacks deal +INT fire damage",
            45,
            lambda: create_item("fire_staff")
        )


class HealingBladeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Healing Blade",
            "Item: On hit, heal nearest ally 50 HP",
            50,
            lambda: create_item("healing_blade")
        )


class CloakOfShadowsAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Cloak of Shadows",
            "Item: Gain 1 dodge every 2 seconds",
            55,
            lambda: create_item("cloak_of_shadows")
        )


class ThrowingKnivesAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Throwing Knives",
            "Item: Attacks hit another random enemy",
            40,
            lambda: create_item("throwing_knives")
        )


class VenomousBladeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Venomous Blade",
            "Item: Attacks apply poison",
            35,
            lambda: create_item("venomous_blade")
        )


class CriticalEdgeAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Critical Edge",
            "Item: Every 4th attack deals 3x damage",
            50,
            lambda: create_item("critical_edge")
        )


class BasiliskHammerAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Basilisk Hammer",
            "Item: On attack deal damage = your armor + MR",
            55,
            lambda: create_item("basilisk_hammer")
        )


class FrostyCloakAugment(ItemAugment):
    def __init__(self):
        super().__init__(
            "Frosty Cloak",
            "Item: Enemies within 3 tiles are chilled",
            50,
            lambda: create_item("frosty_cloak")
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
        # Passive augments (original)
        AttackBoostAugment,
        HealthBoostAugment,
        ArmorBoostAugment,
        AttackSpeedBoostAugment,
        # New global augments
        DefensiveAuraAugment,
        RegenerationFieldAugment,
        FireResistanceAugment,
        DeathsChillAugment,
        PurificationAugment,
        SoulHarvestAugment,
        # Additional new augments
        FlatHealthAugment,
        KnightSynergyAugment,
        WizardSynergyAugment,
        FormationAugment,
        ScalingDamageAugment,
        ScalingDefenseAugment,
        GlobalRegenAugment,
        LowestHPHealAugment,

        # Item augments (original)
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
        # New item augments
        ThunderGlovesAugment,
        LeapBootsAugment,
        ArmorShredderAugment,
        CleavingBladeAugment,
        FireStaffAugment,
        HealingBladeAugment,
        CloakOfShadowsAugment,
        ThrowingKnivesAugment,
        VenomousBladeAugment,
        CriticalEdgeAugment,
        BasiliskHammerAugment,
        FrostyCloakAugment,

        # Rare unit augments
        DragonAugment
    ]


def get_all_passive_augment_types():
    """Returns only passive augment types (for random slot generation)."""
    return [
        AttackBoostAugment,
        HealthBoostAugment,
        ArmorBoostAugment,
        AttackSpeedBoostAugment,
        # New global augments
        DefensiveAuraAugment,
        RegenerationFieldAugment,
        FireResistanceAugment,
        DeathsChillAugment,
        PurificationAugment,
        SoulHarvestAugment,
        # Additional new augments
        FlatHealthAugment,
        KnightSynergyAugment,
        WizardSynergyAugment,
        FormationAugment,
        ScalingDamageAugment,
        ScalingDefenseAugment,
        GlobalRegenAugment,
        LowestHPHealAugment,
    ]


def get_all_item_augment_types():
    """Returns only item augment types."""
    return [
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
        # New item augments
        ThunderGlovesAugment,
        LeapBootsAugment,
        ArmorShredderAugment,
        CleavingBladeAugment,
        FireStaffAugment,
        HealingBladeAugment,
        CloakOfShadowsAugment,
        ThrowingKnivesAugment,
        VenomousBladeAugment,
        CriticalEdgeAugment,
        BasiliskHammerAugment,
        FrostyCloakAugment,
    ]


def generate_augment_shop(team=None, count: int = 10) -> list:
    """Generate a 10-slot shop with the new slot rules.

    Slots 0-1: Always characters
    Slot 2: Always an item
    Slots 3-9: Random (15% char, 30% item, 45% augment, 10% rare unit)
    """
    from content.unit_registry import get_available_units

    shop = []

    # Helper to generate a character entry
    # Cost is calculated dynamically based on team's current unit count
    def gen_character():
        unit_type = random.choice(get_available_units())
        return CharacterShopEntry(unit_type, team)

    # Helper to generate an item entry
    def gen_item():
        item_types = get_all_item_augment_types()
        return random.choice(item_types)()

    # Helper to generate a passive augment
    def gen_augment():
        augment_types = get_all_passive_augment_types()
        return random.choice(augment_types)()

    # Slots 0-1: Always characters
    for _ in range(2):
        shop.append(gen_character())

    # Slot 2: Always an item
    shop.append(gen_item())

    # Slots 3-9: Random with weights (20% char, 30% item, 40% augment, 10% rare)
    for _ in range(7):
        roll = random.random()
        if roll < 0.20:  # 20% character
            shop.append(gen_character())
        elif roll < 0.50:  # 30% item
            shop.append(gen_item())
        elif roll < 0.90:  # 40% augment
            shop.append(gen_augment())
        else:  # 10% rare unit augment (dragon, etc)
            shop.append(DragonAugment())

    # Sort shop by type: units first, then items, then augments
    def sort_key(entry):
        if isinstance(entry, CharacterShopEntry):
            return 0  # Units first
        elif isinstance(entry, ItemAugment):
            return 1  # Items second
        elif isinstance(entry, PassiveAugment):
            return 2  # Augments third
        elif isinstance(entry, UnitAugment):
            return 3  # Rare units last
        return 4

    shop.sort(key=sort_key)

    return shop


def generate_augment_shop_legacy(count: int = 5) -> list:
    """Legacy shop generation for enemy teams."""
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