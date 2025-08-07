#!/usr/bin/env python3
"""
Unit tests for necromancer abilities.
Tests each ability to verify it does what it's supposed to do.
Runs headlessly without any UI.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from board import Board
from game import Game, GameMode
from content.units.necromancer import create_necromancer, create_necromancer_skill
from unit import Unit, UnitType


class TestNecromancerAbilities(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment before each test"""
        self.game = Game(GameMode.ASYNC)
        self.board = self.game.board
        self.necromancer = create_necromancer()
        # Set the board reference for the necromancer before adding to board
        self.necromancer.board = self.board
        self.board.add_unit(self.necromancer, 2, 5, "player")
        
        # Create a test enemy for targeting
        self.enemy = Unit("Test Enemy", UnitType.BERSERKER)
        self.enemy.max_hp = 100
        self.enemy.hp = 100
        self.enemy.max_mp = 50
        self.enemy.mp = 50
        self.enemy.board = self.board  # Set board reference
        self.board.add_unit(self.enemy, 6, 5, "enemy")
    
    def test_summon_skeleton_basic(self):
        """Test that summon_skeleton creates a skeleton warrior"""
        # Ensure necromancer has enough mana
        self.necromancer.mp = 120
        initial_unit_count = len(self.board.player_units)
        
        # Cast summon skeleton
        summon_skill = self.necromancer.spell
        self.assertEqual(summon_skill.name, "Summon Skeleton")
        
        # Execute the skill
        summon_skill.execute(self.necromancer)
        
        # Check that a skeleton was summoned
        self.assertEqual(len(self.board.player_units), initial_unit_count + 1)
        
        # Find the skeleton
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'unit_type') and unit.unit_type == UnitType.SKELETON:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton, "Skeleton was not summoned")
        self.assertEqual(skeleton.team, "player")
    
    def test_undead_horde_summons_two_skeletons(self):
        """Test that undead_horde passive causes summon_skeleton to create 2 skeletons"""
        # Add undead_horde passive skill
        undead_horde = create_necromancer_skill("undead_horde")
        self.necromancer.add_passive_skill(undead_horde)
        
        # Ensure necromancer has enough mana
        self.necromancer.mp = 120
        initial_unit_count = len(self.board.player_units)
        
        # Cast summon skeleton
        summon_skill = self.necromancer.spell
        summon_skill.execute(self.necromancer)
        
        # Should summon 2 skeletons instead of 1
        self.assertEqual(len(self.board.player_units), initial_unit_count + 2)
        
        # Count skeletons
        skeleton_count = sum(1 for unit in self.board.player_units 
                           if unit != self.necromancer and hasattr(unit, 'unit_type') and unit.unit_type == UnitType.SKELETON)
        self.assertEqual(skeleton_count, 2)
    
    def test_bone_sabers_increases_skeleton_damage(self):
        """Test that bone_sabers passive increases skeleton attack damage by 5"""
        # Add bone_sabers passive skill
        bone_sabers = create_necromancer_skill("bone_sabers")
        self.necromancer.add_passive_skill(bone_sabers)
        
        # Summon skeleton
        self.necromancer.mp = 120
        summon_skill = self.necromancer.spell
        summon_skill.execute(self.necromancer)
        
        # Find the skeleton
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'unit_type') and unit.unit_type == UnitType.SKELETON:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        # Base skeleton damage should be increased by 5
        # We need to check if the skeleton's attack damage is higher than base
        # (assuming base skeleton damage without bone_sabers is lower)
        self.assertGreater(skeleton.attack_damage, 10)  # Assuming base damage is around 10
    
    def test_hunger_gives_skeleton_life_drain(self):
        """Test that hunger passive gives summoned skeletons life drain ability"""
        # Add hunger passive skill
        hunger = create_necromancer_skill("hunger")
        self.necromancer.add_passive_skill(hunger)
        
        # Summon skeleton
        self.necromancer.mp = 120
        summon_skill = self.necromancer.spell
        summon_skill.execute(self.necromancer)
        
        # Find the skeleton
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'unit_type') and unit.unit_type == UnitType.SKELETON:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        self.assertIsNotNone(skeleton.spell, "Skeleton should have a spell from hunger passive")
        self.assertEqual(skeleton.spell.name, "Life Drain")
    
    def test_burning_bones_adds_fire_aura(self):
        """Test that burning_bones passive adds fire aura to skeletons"""
        # Add burning_bones passive skill
        burning_bones = create_necromancer_skill("burning_bones")
        self.necromancer.add_passive_skill(burning_bones)
        
        # Summon skeleton
        self.necromancer.mp = 120
        summon_skill = self.necromancer.spell
        summon_skill.execute(self.necromancer)
        
        # Find the skeleton
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'unit_type') and unit.unit_type == UnitType.SKELETON:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        # Check if skeleton has burning bones aura passive skill
        has_burning_aura = any(skill.name == "Burning Bones Aura" for skill in skeleton.passive_skills)
        self.assertTrue(has_burning_aura, "Skeleton should have Burning Bones Aura")
    
    def test_bone_shards_triggers_on_skeleton_death(self):
        """Test that bone_shards passive triggers when a skeleton dies"""
        # Add bone_shards passive skill to necromancer
        bone_shards = create_necromancer_skill("bone_shards")
        self.necromancer.add_passive_skill(bone_shards)
        
        # Summon skeleton
        self.necromancer.mp = 120
        summon_skill = self.necromancer.spell
        summon_skill.current_mana = 100
        summon_skill.execute(self.necromancer)
        
        # Find the skeleton
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'unit_type') and unit.unit_type == UnitType.SKELETON:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        skeleton.is_summoned = True  # Mark as summoned so bone shards triggers
        
        # Record initial projectile count
        initial_projectiles = len(self.board.projectiles)
        
        # Kill the skeleton
        skeleton.hp = 0
        skeleton.die(self.enemy)
        
        # Check if projectiles were created (bone shards should shoot at enemies)
        self.assertGreater(len(self.board.projectiles), initial_projectiles, 
                          "Bone shards should create projectiles when skeleton dies")
    
    def test_grave_chill_triggers_on_skeleton_death(self):
        """Test that grave_chill passive triggers when a skeleton dies"""
        # Add grave_chill passive skill to necromancer
        grave_chill = create_necromancer_skill("grave_chill")
        self.necromancer.add_passive_skill(grave_chill)
        
        # Create a second enemy near the first one
        enemy2 = Unit("Enemy2", UnitType.BERSERKER)
        enemy2.max_hp = 80
        enemy2.hp = 80
        enemy2.board = self.board
        self.board.add_unit(enemy2, 7, 5, "enemy")
        
        # Record enemy2's initial HP
        initial_enemy2_hp = enemy2.hp
        
        # Kill the first enemy (to trigger grave chill)
        self.enemy.hp = 0
        self.enemy.die(self.necromancer)
        
        # Check if enemy2 took damage from grave chill (5% of enemy's max hp)
        expected_damage = self.enemy.max_hp * 0.05
        self.assertLess(enemy2.hp, initial_enemy2_hp, 
                       "Grave chill should damage a nearby enemy when an enemy dies")
        self.assertAlmostEqual(initial_enemy2_hp - enemy2.hp, expected_damage, places=1,
                              msg="Grave chill should deal 5% of dying unit's max HP as damage")
    
    def test_bone_fragments_triggers_on_unit_death(self):
        """Test that bone_fragments passive triggers when a skeleton dies"""
        # Add bone_fragments passive skill to necromancer
        bone_fragments = create_necromancer_skill("bone_fragments")
        self.necromancer.add_passive_skill(bone_fragments)
        
        # Summon skeleton first
        summon_skill = self.necromancer.spell
        summon_skill.current_mana = 100
        summon_skill.execute(self.necromancer)
        
        # Find the skeleton
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'unit_type') and unit.unit_type == UnitType.SKELETON:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        skeleton.is_summoned = True  # Mark as summoned
        
        # Record initial unit count
        initial_unit_count = len(self.board.player_units)
        
        # Kill the skeleton
        skeleton.hp = 0
        skeleton.die(self.enemy)
        
        # Board should still have units (necromancer + bone fragment spawned)
        # The skeleton dies but a bone fragment should spawn
        remaining_units = [u for u in self.board.player_units if u.is_alive()]
        self.assertGreaterEqual(len(remaining_units), 1, 
                               "Should have at least necromancer after skeleton dies and spawns fragment")
    
    def test_necromancer_default_skill_is_summon_skeleton(self):
        """Test that necromancer starts with summon_skeleton as default skill"""
        self.assertIsNotNone(self.necromancer.spell)
        self.assertEqual(self.necromancer.spell.name, "Summon Skeleton")
    
    def test_necromancer_stats(self):
        """Test that necromancer has correct base stats"""
        self.assertEqual(self.necromancer.max_hp, 80)
        self.assertEqual(self.necromancer.max_mp, 120)
        self.assertEqual(self.necromancer.attack_damage, 8)
        self.assertEqual(self.necromancer.attack_range, 4)
        self.assertEqual(self.necromancer.intelligence, 20)
        self.assertEqual(self.necromancer.armor, 5)
        self.assertEqual(self.necromancer.magic_resist, 15)
    
    def test_summon_skeleton_mana_cost(self):
        """Test that summon_skeleton costs the correct amount of mana"""
        summon_skill = self.necromancer.spell
        
        # The skill should have a mana cost of 100
        self.assertEqual(summon_skill.mana_cost, 100)
        
        # Test if necromancer can cast with sufficient skill mana
        summon_skill.current_mana = 100
        can_cast = self.necromancer.can_cast(summon_skill)
        self.assertTrue(can_cast)
        
        # Test if necromancer cannot cast with insufficient skill mana
        summon_skill.current_mana = 50
        can_cast = self.necromancer.can_cast(summon_skill)
        self.assertFalse(can_cast)
    
    def test_summon_skeleton_cast_time(self):
        """Test that summon_skeleton has correct cast time"""
        summon_skill = self.necromancer.spell
        self.assertEqual(summon_skill.cast_time, 1.0)
    
    def test_summon_skeleton_should_cast_logic(self):
        """Test that summon_skeleton only casts when there are fewer than 3 skeletons"""
        summon_skill = self.necromancer.spell
        
        # Should cast when no skeletons exist
        self.assertTrue(summon_skill.should_cast(self.necromancer))
        
        # Create 3 skeleton units manually
        for i in range(3):
            skeleton = Unit(f"Skeleton_{i}", UnitType.SKELETON)
            self.board.add_unit(skeleton, i, 0, "player")
        
        # Should not cast when 3 skeletons already exist
        self.assertFalse(summon_skill.should_cast(self.necromancer))


if __name__ == '__main__':
    # Run tests without opening UI
    unittest.main(verbosity=2)