import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from game import Game, GameMode
from unit import Unit, UnitType


class TestEnemyPositioning(unittest.TestCase):

    def test_melee_units_in_front_rows(self):
        """Melee units (attack_range <= 1) should be placed in x=4-5"""
        game = Game(GameMode.ASYNC)

        # Create melee units
        melee_units = []
        for i in range(4):
            unit = Unit(f"Melee{i}", UnitType.BERSERKER)
            unit.attack_range = 1
            melee_units.append(unit)

        positions = game._generate_strategic_positions(melee_units)

        print(f"Melee positions: {positions}")

        for i, pos in enumerate(positions):
            self.assertIn(pos[0], [4, 5], f"Melee unit {i} at x={pos[0]}, expected 4 or 5")
            self.assertIn(pos[1], range(8), f"Melee unit {i} at y={pos[1]}, expected 0-7")

    def test_ranged_units_in_back_rows(self):
        """Ranged units (attack_range > 1) should be placed in x=6-7"""
        game = Game(GameMode.ASYNC)

        # Create ranged units
        ranged_units = []
        for i in range(4):
            unit = Unit(f"Ranged{i}", UnitType.PYROMANCER)
            unit.attack_range = 4
            ranged_units.append(unit)

        positions = game._generate_strategic_positions(ranged_units)

        print(f"Ranged positions: {positions}")

        for i, pos in enumerate(positions):
            self.assertIn(pos[0], [6, 7], f"Ranged unit {i} at x={pos[0]}, expected 6 or 7")
            self.assertIn(pos[1], range(8), f"Ranged unit {i} at y={pos[1]}, expected 0-7")

    def test_mixed_units_positioning(self):
        """Mixed melee/ranged units should be placed correctly"""
        game = Game(GameMode.ASYNC)

        # Create mixed units - Cleric (range 3) and Assassin (range 1)
        cleric = Unit("Cleric", UnitType.CLERIC)
        cleric.attack_range = 3  # Ranged

        assassin = Unit("Assassin", UnitType.ASSASSIN)
        assassin.attack_range = 1  # Melee

        units = [cleric, assassin]
        positions = game._generate_strategic_positions(units)

        print(f"Cleric (range 3) position: {positions[0]}")
        print(f"Assassin (range 1) position: {positions[1]}")

        # Cleric should be in back (x=6-7)
        self.assertIn(positions[0][0], [6, 7], f"Cleric at x={positions[0][0]}, expected 6 or 7")

        # Assassin should be in front (x=4-5)
        self.assertIn(positions[1][0], [4, 5], f"Assassin at x={positions[1][0]}, expected 4 or 5")

    def test_y_positions_are_random(self):
        """Y positions should vary across multiple runs"""
        game = Game(GameMode.ASYNC)

        y_values_seen = set()

        for _ in range(20):
            unit = Unit("Test", UnitType.BERSERKER)
            unit.attack_range = 1
            positions = game._generate_strategic_positions([unit])
            y_values_seen.add(positions[0][1])

        print(f"Y values seen across 20 runs: {sorted(y_values_seen)}")

        # Should see at least 3 different y values across 20 runs
        self.assertGreaterEqual(len(y_values_seen), 3,
            f"Expected varied y positions, only saw {y_values_seen}")

    def test_no_position_collisions(self):
        """Multiple units should not share the same position"""
        game = Game(GameMode.ASYNC)

        # Create many units to fill positions
        units = []
        for i in range(8):
            unit = Unit(f"Unit{i}", UnitType.BERSERKER)
            unit.attack_range = 1
            units.append(unit)

        positions = game._generate_strategic_positions(units)

        print(f"Positions for 8 melee units: {positions}")

        # Check no duplicates
        self.assertEqual(len(positions), len(set(positions)),
            f"Found duplicate positions: {positions}")

    def test_actual_cleric_and_assassin_classes(self):
        """Test with actual Cleric and Assassin unit classes"""
        from content.units.cleric import Cleric
        from content.units.assassin import Assassin

        game = Game(GameMode.ASYNC)

        cleric = Cleric()
        assassin = Assassin()

        print(f"Cleric attack_range: {cleric.attack_range}")
        print(f"Assassin attack_range: {assassin.attack_range}")

        units = [cleric, assassin]
        positions = game._generate_strategic_positions(units)

        print(f"Cleric position: {positions[0]}")
        print(f"Assassin position: {positions[1]}")

        # Cleric has range 3, should be in back
        self.assertIn(positions[0][0], [6, 7],
            f"Cleric (range {cleric.attack_range}) at x={positions[0][0]}, expected 6 or 7")

        # Assassin has range 1, should be in front
        self.assertIn(positions[1][0], [4, 5],
            f"Assassin (range {assassin.attack_range}) at x={positions[1][0]}, expected 4 or 5")


    def test_full_game_flow_positioning(self):
        """Test that enemy units are properly positioned after full game flow"""
        game = Game(GameMode.ASYNC)
        game.start_new_round()

        print("\n--- Full game flow test ---")
        print(f"Enemy units: {len(game.enemy_team.units)}")

        for unit in game.enemy_team.units:
            print(f"  {unit.name} (range {unit.attack_range}): "
                  f"board pos ({unit.x}, {unit.y}), "
                  f"original ({unit.original_x}, {unit.original_y})")

            # Check that board position matches original position
            self.assertEqual(unit.x, unit.original_x,
                f"{unit.name} x mismatch: board={unit.x}, original={unit.original_x}")
            self.assertEqual(unit.y, unit.original_y,
                f"{unit.name} y mismatch: board={unit.y}, original={unit.original_y}")

            # Check that melee units are in front (x=4-5)
            if unit.attack_range <= 1:
                self.assertIn(unit.x, [4, 5],
                    f"Melee {unit.name} at x={unit.x}, expected 4-5")
            # Check that ranged units are in back (x=6-7)
            else:
                self.assertIn(unit.x, [6, 7],
                    f"Ranged {unit.name} at x={unit.x}, expected 6-7")


if __name__ == '__main__':
    unittest.main(verbosity=2)
