#!/usr/bin/env python3
"""
Comprehensive tests for necromancer abilities.
Tests active skills to verify they work correctly.
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


if __name__ == '__main__':
    # Run tests without opening UI
    unittest.main(verbosity=2)
