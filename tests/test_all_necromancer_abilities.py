#!/usr/bin/env python3
"""
Comprehensive tests for all necromancer abilities.
Tests both active and passive skills to verify they work correctly.
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


class TestAllNecromancerAbilities(unittest.TestCase):
    
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
    
    def test_summon_skeleton_creates_skeleton(self):
        """Test basic skeleton summoning"""
        skill = create_necromancer_skill("summon_skeleton")
        skill.owner = self.necromancer
        skill.current_mana = 100
        
        initial_count = len(self.board.player_units)
        skill.execute(self.necromancer)
        
        self.assertEqual(len(self.board.player_units), initial_count + 1)
        
        # Find the skeleton
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'name') and "Skeleton" in unit.name:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        self.assertEqual(skeleton.team, "player")
    
    
    
    
    
    
    
    
    def test_undead_horde_summons_multiple_skeletons(self):
        """Test that undead_horde passive causes multiple skeleton summoning"""
        # Add undead horde passive
        undead_horde = create_necromancer_skill("undead_horde")
        self.necromancer.add_passive_skill(undead_horde)
        
        summon_skill = create_necromancer_skill("summon_skeleton")
        summon_skill.owner = self.necromancer
        summon_skill.current_mana = 100
        
        initial_count = len(self.board.player_units)
        summon_skill.execute(self.necromancer)
        
        # Should summon 2 skeletons instead of 1
        self.assertEqual(len(self.board.player_units), initial_count + 2)
    
    def test_bone_sabers_increases_skeleton_damage(self):
        """Test that bone_sabers passive increases skeleton damage"""
        # Add bone sabers passive
        bone_sabers = create_necromancer_skill("bone_sabers")
        self.necromancer.add_passive_skill(bone_sabers)
        
        summon_skill = create_necromancer_skill("summon_skeleton")
        summon_skill.owner = self.necromancer
        summon_skill.current_mana = 100
        summon_skill.execute(self.necromancer)
        
        # Find skeleton and check damage
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'name') and "Skeleton" in unit.name:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        # Should have increased damage from bone sabers
        self.assertGreaterEqual(skeleton.attack_damage, 13)  # Base 8 + 5 from bone sabers
    
    def test_hunger_gives_skeleton_life_drain(self):
        """Test that hunger passive gives skeletons life drain spell"""
        # Add hunger passive
        hunger = create_necromancer_skill("hunger")
        self.necromancer.add_passive_skill(hunger)
        
        summon_skill = create_necromancer_skill("summon_skeleton")
        summon_skill.owner = self.necromancer
        summon_skill.current_mana = 100
        summon_skill.execute(self.necromancer)
        
        # Find skeleton and check spell
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'name') and "Skeleton" in unit.name:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        self.assertIsNotNone(skeleton.spell)
        self.assertEqual(skeleton.spell.name, "Life Drain")
    
    def test_burning_bones_adds_aura_to_skeletons(self):
        """Test that burning_bones passive adds fire aura to skeletons"""
        # Add burning bones passive
        burning_bones = create_necromancer_skill("burning_bones")
        self.necromancer.add_passive_skill(burning_bones)
        
        summon_skill = create_necromancer_skill("summon_skeleton")
        summon_skill.owner = self.necromancer
        summon_skill.current_mana = 100
        summon_skill.execute(self.necromancer)
        
        # Find skeleton and check for aura
        skeleton = None
        for unit in self.board.player_units:
            if unit != self.necromancer and hasattr(unit, 'name') and "Skeleton" in unit.name:
                skeleton = unit
                break
        
        self.assertIsNotNone(skeleton)
        
        # Check if skeleton has burning bones aura
        has_aura = any(skill.name == "Burning Bones Aura" for skill in skeleton.passive_skills)
        self.assertTrue(has_aura)


if __name__ == '__main__':
    # Run tests without opening UI
    unittest.main(verbosity=2)