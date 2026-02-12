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

    def test_necromancer_default_skill_is_summon_skeleton(self):
        """Test that necromancer starts with summon_skeleton as default skill"""
        self.assertIsNotNone(self.necromancer.spell)
        self.assertEqual(self.necromancer.spell.name, "Summon Skeleton")

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
