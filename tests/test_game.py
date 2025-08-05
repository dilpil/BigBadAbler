#!/usr/bin/env python3
"""
Unit tests for BigBadAbler game components.
Tests basic stability and functionality without requiring UI.
"""

import unittest
import sys
import os

# Add the parent directory (game root) to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from board import Board
from unit import Unit
from game import Game, GamePhase, GameMode
from content.units import create_unit, get_available_units
from content.items import generate_item_shop
from constants import FRAME_TIME


class TestBoardSanity(unittest.TestCase):
    """Test that the board can handle basic operations without crashing."""
    
    def setUp(self):
        """Set up a fresh board for each test."""
        self.board = Board()
    
    def test_board_basic_operations(self):
        """Test basic board operations don't crash."""
        # Create some test units
        necromancer = create_unit("necromancer")
        paladin = create_unit("paladin")
        pyromancer = create_unit("pyromancer")
        
        # Place units on board
        self.assertTrue(self.board.add_unit(necromancer, 1, 1, "player"))
        self.assertTrue(self.board.add_unit(paladin, 2, 2, "player"))
        self.assertTrue(self.board.add_unit(pyromancer, 8, 8, "enemy"))
        
        # Verify units are placed correctly
        self.assertEqual(len(self.board.player_units), 2)
        self.assertEqual(len(self.board.enemy_units), 1)
        self.assertEqual(self.board.get_unit_at(1, 1), necromancer)
        
        # Test moving units
        self.assertTrue(self.board.move_unit(necromancer, 3, 3))
        self.assertEqual(necromancer.x, 3)
        self.assertEqual(necromancer.y, 3)
    
    def test_board_1000_updates_no_crash(self):
        """Test that board can handle 1000 updates without crashing."""
        # Create and place units
        necromancer = create_unit("necromancer")
        paladin = create_unit("paladin")
        pyromancer = create_unit("pyromancer")
        berserker = create_unit("berserker")
        
        self.board.add_unit(necromancer, 1, 1, "player")
        self.board.add_unit(paladin, 2, 2, "player")
        self.board.add_unit(pyromancer, 8, 8, "enemy")
        self.board.add_unit(berserker, 9, 9, "enemy")
        
        # Set board references for units
        for unit in self.board.get_all_units():
            unit.board = self.board
        
        # Run 1000 updates
        for i in range(1000):
            try:
                self.board.update_combat(FRAME_TIME)
                # Every 100 frames, verify we still have units
                if i % 100 == 0:
                    self.assertGreater(len(self.board.get_all_units()), 0)
            except Exception as e:
                self.fail(f"Board crashed on update {i}: {e}")


class TestGameSanity(unittest.TestCase):
    """Test that the game can handle basic operations without crashing."""
    
    def setUp(self):
        """Set up a fresh game for each test."""
        self.game = Game(GameMode.ASYNC)
        # Set up the game properly
        self.game.available_units = get_available_units()
        self.game.available_items = generate_item_shop()
        
        # Override create methods
        from content.units import create_unit
        from skill_factory import create_skill
        self.game.create_unit = create_unit
        self.game.create_skill = create_skill
        
        # Override cost methods  
        from content.units import get_unit_cost
        from skill_factory import get_skill_cost
        self.game.get_unit_cost = get_unit_cost
        self.game.get_skill_cost = get_skill_cost
        
        self.game.start_new_round()
    
    def test_game_setup_and_purchase(self):
        """Test basic game setup and unit purchasing."""
        # Verify initial state
        self.assertEqual(self.game.phase, GamePhase.SHOPPING)
        self.assertEqual(self.game.gold, 100)
        self.assertEqual(self.game.round, 1)
        
        # Purchase some units
        self.assertTrue(self.game.purchase_unit("necromancer", 1, 1))
        self.assertTrue(self.game.purchase_unit("paladin", 2, 2))
        
        # Verify purchases
        self.assertEqual(len(self.game.owned_units), 2)
        self.assertEqual(self.game.gold, 0)  # 100 - 50 - 50 = 0
        
        # Verify units are on board
        self.assertEqual(len(self.game.board.player_units), 2)
    
    def test_game_1000_combat_updates_no_crash(self):
        """Test that game can handle 1000 combat updates without crashing."""
        # Set up units
        self.game.purchase_unit("necromancer", 1, 1)
        self.game.purchase_unit("paladin", 2, 2)
        
        # Start combat
        self.game.start_combat()
        self.assertEqual(self.game.phase, GamePhase.COMBAT)
        
        # Run 1000 combat updates
        for i in range(1000):
            try:
                self.game.update_combat(FRAME_TIME)
                
                # Every 100 frames, check if combat ended naturally
                if i % 100 == 0:
                    if self.game.phase == GamePhase.SHOPPING:
                        # Combat ended naturally, this is fine
                        break
                        
            except Exception as e:
                self.fail(f"Game crashed on combat update {i}: {e}")


class TestGameRoundReset(unittest.TestCase):
    """Test that the game properly resets units between rounds."""
    
    def setUp(self):
        """Set up a game with proper initialization."""
        self.game = Game(GameMode.ASYNC)
        self.game.available_units = get_available_units()
        self.game.available_items = generate_item_shop()
        
        from content.units import create_unit, get_unit_cost
        from skill_factory import create_skill, get_skill_cost
        self.game.create_unit = create_unit
        self.game.create_skill = create_skill
        self.game.get_unit_cost = get_unit_cost
        self.game.get_skill_cost = get_skill_cost
        
        self.game.start_new_round()
    
    def test_three_round_cycle(self):
        """Test that the game can run three complete rounds without issues."""
        # Buy two units initially
        self.assertTrue(self.game.purchase_unit("necromancer", 1, 1))
        self.assertTrue(self.game.purchase_unit("paladin", 2, 2))
        
        initial_units = len(self.game.owned_units)
        self.assertEqual(initial_units, 2)
        
        for round_num in range(1, 4):  # Rounds 1, 2, 3
            with self.subTest(round=round_num):
                # Verify we're in shopping phase
                self.assertEqual(self.game.phase, GamePhase.SHOPPING)
                self.assertEqual(self.game.round, round_num)
                
                # Verify units are properly reset
                for unit in self.game.owned_units:
                    self.assertEqual(unit.hp, unit.max_hp, f"Unit {unit.name} not at full HP in round {round_num}")
                    self.assertEqual(unit.mp, unit.max_mp, f"Unit {unit.name} not at full MP in round {round_num}")
                    self.assertIsNone(unit.target, f"Unit {unit.name} still has target in round {round_num}")
                    self.assertEqual(unit.attack_timer, 0, f"Unit {unit.name} has attack timer in round {round_num}")
                
                # Verify units are back at original positions
                necromancer = next((u for u in self.game.owned_units if u.unit_type == "necromancer"), None)
                paladin = next((u for u in self.game.owned_units if u.unit_type == "paladin"), None)
                
                self.assertIsNotNone(necromancer)
                self.assertIsNotNone(paladin)
                self.assertEqual((necromancer.x, necromancer.y), (1, 1))
                self.assertEqual((paladin.x, paladin.y), (2, 2))
                
                # Start combat
                self.game.start_combat()
                self.assertEqual(self.game.phase, GamePhase.COMBAT)
                
                # Force combat to end by running many updates or manually ending
                max_updates = 1000
                for i in range(max_updates):
                    if self.game.phase == GamePhase.SHOPPING:
                        break
                    self.game.update_combat(FRAME_TIME)
                
                # If combat didn't end naturally, force it to end
                if self.game.phase == GamePhase.COMBAT:
                    # Manually end combat for testing
                    self.game.end_combat()
                
                # Verify we're back in shopping phase (unless game over)
                if not self.game.is_game_over():
                    self.assertEqual(self.game.phase, GamePhase.SHOPPING)
                else:
                    # Game over is acceptable outcome
                    break
        
        # Verify we still have our original units (they should persist across rounds)
        self.assertEqual(len(self.game.owned_units), initial_units)


class TestUnitPersistence(unittest.TestCase):
    """Test that units don't mysteriously disappear across multiple rounds."""
    
    def setUp(self):
        """Set up a game with proper initialization."""
        self.game = Game(GameMode.ASYNC)
        self.game.available_units = get_available_units()
        self.game.available_items = generate_item_shop()
        
        from content.units import create_unit, get_unit_cost
        from skill_factory import create_skill, get_skill_cost
        self.game.create_unit = create_unit
        self.game.create_skill = create_skill
        self.game.get_unit_cost = get_unit_cost
        self.game.get_skill_cost = get_skill_cost
        
        self.game.start_new_round()
    
    def test_unit_persistence_across_five_rounds(self):
        """Test that units persist correctly across 5 rounds with detailed tracking."""
        purchased_units = []  # Track what we buy each round
        
        for round_num in range(1, 6):  # Rounds 1-5
            with self.subTest(round=round_num):
                print(f"\n=== ROUND {round_num} ===")
                
                # Verify we're in shopping phase
                self.assertEqual(self.game.phase, GamePhase.SHOPPING)
                self.assertEqual(self.game.round, round_num)
                
                # Check that all previously purchased units are still present
                expected_unit_count = len(purchased_units)
                actual_unit_count = len(self.game.owned_units)
                
                print(f"Expected units: {expected_unit_count}, Actual units: {actual_unit_count}")
                
                if expected_unit_count != actual_unit_count:
                    print(f"ERROR: Unit count mismatch in round {round_num}")
                    print(f"Expected units from previous rounds: {[u['type'] for u in purchased_units]}")
                    print(f"Actual units present: {[u.unit_type for u in self.game.owned_units]}")
                    
                    # Check which specific units are missing
                    expected_types = [u['type'] for u in purchased_units]
                    actual_types = [u.unit_type for u in self.game.owned_units]
                    
                    for expected_type in expected_types:
                        count_expected = expected_types.count(expected_type)
                        count_actual = actual_types.count(expected_type)
                        if count_expected != count_actual:
                            print(f"Missing {expected_type}: expected {count_expected}, found {count_actual}")
                
                self.assertEqual(actual_unit_count, expected_unit_count, 
                               f"Units disappeared between rounds! Expected {expected_unit_count}, got {actual_unit_count}")
                
                # Verify each previously purchased unit is still there with correct properties
                for i, unit_info in enumerate(purchased_units):
                    found_unit = None
                    for unit in self.game.owned_units:
                        if (unit.unit_type == unit_info['type'] and 
                            unit.original_x == unit_info['x'] and 
                            unit.original_y == unit_info['y']):
                            found_unit = unit
                            break
                    
                    self.assertIsNotNone(found_unit, 
                                       f"Unit {unit_info['type']} at ({unit_info['x']}, {unit_info['y']}) disappeared!")
                    
                    # Verify unit is properly reset for new round
                    self.assertEqual(found_unit.hp, found_unit.max_hp, 
                                   f"Unit {found_unit.unit_type} not at full HP")
                    self.assertEqual(found_unit.mp, found_unit.max_mp, 
                                   f"Unit {found_unit.unit_type} not at full MP")
                    self.assertEqual(found_unit.x, unit_info['x'], 
                                   f"Unit {found_unit.unit_type} not at original X position")
                    self.assertEqual(found_unit.y, unit_info['y'], 
                                   f"Unit {found_unit.unit_type} not at original Y position")
                
                # Buy 1-2 new units this round (if we have space and gold)
                available_positions = [(x, y) for x in range(5) for y in range(10) 
                                     if not self.game.board.get_unit_at(x, y)]
                
                units_to_buy = min(2, len(available_positions), self.game.gold // 50)
                
                for i in range(units_to_buy):
                    unit_types = ["necromancer", "paladin", "pyromancer", "berserker"]
                    unit_type = unit_types[round_num % len(unit_types)]  # Rotate through types
                    pos = available_positions[i]
                    
                    purchase_success = self.game.purchase_unit(unit_type, pos[0], pos[1])
                    self.assertTrue(purchase_success, f"Failed to purchase {unit_type} in round {round_num}")
                    
                    # Track this purchase
                    unit_info = {
                        'type': unit_type,
                        'x': pos[0],
                        'y': pos[1],
                        'round_purchased': round_num
                    }
                    purchased_units.append(unit_info)
                    print(f"Purchased {unit_type} at ({pos[0]}, {pos[1]})")
                
                print(f"Total units after purchases: {len(self.game.owned_units)}")
                print(f"Units on board (player): {len(self.game.board.player_units)}")
                
                # Verify the purchase worked
                self.assertEqual(len(self.game.owned_units), len(purchased_units))
                self.assertEqual(len(self.game.board.player_units), len(purchased_units))
                
                # Start combat
                print("Starting combat...")
                self.game.start_combat()
                self.assertEqual(self.game.phase, GamePhase.COMBAT)
                
                # Run combat for a reasonable number of updates
                max_combat_updates = 500
                for i in range(max_combat_updates):
                    if self.game.phase == GamePhase.SHOPPING:
                        print(f"Combat ended naturally after {i} updates")
                        break
                    self.game.update_combat(FRAME_TIME)
                    
                    # Sanity check during combat - units shouldn't disappear mid-fight
                    if i % 100 == 0:  # Check every 100 frames
                        player_units_in_combat = len(self.game.board.player_units)
                        # Units can die in combat, but owned_units should remain the same
                        self.assertEqual(len(self.game.owned_units), len(purchased_units),
                                       f"Units disappeared during combat at frame {i}")
                
                # Force end combat if it didn't end naturally
                if self.game.phase == GamePhase.COMBAT:
                    print("Forcing combat to end...")
                    self.game.end_combat()
                
                # After combat, verify we're back in shopping and units are still there
                if not self.game.is_game_over():
                    self.assertEqual(self.game.phase, GamePhase.SHOPPING)
                    post_combat_units = len(self.game.owned_units)
                    print(f"Units after combat: {post_combat_units}")
                    
                    self.assertEqual(post_combat_units, len(purchased_units),
                                   f"Units lost after combat in round {round_num}")
                else:
                    print("Game over - ending test")
                    break
        
        print(f"\nFinal summary:")
        print(f"Total units purchased: {len(purchased_units)}")
        print(f"Final unit count: {len(self.game.owned_units)}")
        print(f"Units by type: {[(u.unit_type, u.original_x, u.original_y) for u in self.game.owned_units]}")
    
    def test_unit_persistence_with_deaths_and_summons(self):
        """Test unit persistence when units die and summons are created."""
        # Buy necromancers who can summon units
        self.game.purchase_unit("necromancer", 0, 0)
        self.game.purchase_unit("necromancer", 1, 1)
        
        initial_owned_units = len(self.game.owned_units)  # Should be 2
        
        for round_num in range(1, 4):  # 3 rounds
            with self.subTest(round=round_num):
                print(f"\n=== ROUND {round_num} (Deaths & Summons Test) ===")
                
                # Track units before combat
                pre_combat_owned = len(self.game.owned_units)
                pre_combat_on_board = len(self.game.board.player_units)
                
                print(f"Pre-combat: {pre_combat_owned} owned, {pre_combat_on_board} on board")
                
                # Start combat - necromancers might summon skeletons
                self.game.start_combat()
                
                # Run combat long enough for potential summons and deaths
                for i in range(1000):
                    if self.game.phase == GamePhase.SHOPPING:
                        break
                    self.game.update_combat(FRAME_TIME)
                    
                    # Check every 250 frames
                    if i % 250 == 0:
                        mid_combat_owned = len(self.game.owned_units)
                        mid_combat_on_board = len(self.game.board.player_units)
                        print(f"Mid-combat frame {i}: {mid_combat_owned} owned, {mid_combat_on_board} on board")
                        
                        # Owned units should never change during combat
                        self.assertEqual(mid_combat_owned, pre_combat_owned,
                                       f"Owned units changed during combat at frame {i}")
                
                # Force end if needed
                if self.game.phase == GamePhase.COMBAT:
                    self.game.end_combat()
                
                if self.game.is_game_over():
                    break
                
                # After combat, owned units should be the same
                post_combat_owned = len(self.game.owned_units)
                post_combat_on_board = len(self.game.board.player_units)
                
                print(f"Post-combat: {post_combat_owned} owned, {post_combat_on_board} on board")
                
                self.assertEqual(post_combat_owned, initial_owned_units,
                               f"Owned units changed after round {round_num}")
                self.assertEqual(post_combat_on_board, initial_owned_units,
                               f"Board units don't match owned units after round {round_num}")
    
    def test_unit_persistence_stress_test(self):
        """Stress test with many units and rapid round cycling."""
        purchased_units = []
        max_units = 20  # Buy more units than normal
        
        # Fill up the board quickly
        positions = [(x, y) for x in range(5) for y in range(10)]
        unit_types = ["necromancer", "paladin", "pyromancer", "berserker"]
        
        for i in range(min(max_units, len(positions))):
            if self.game.gold < 50:
                break
                
            unit_type = unit_types[i % len(unit_types)]
            pos = positions[i]
            
            if self.game.purchase_unit(unit_type, pos[0], pos[1]):
                purchased_units.append({
                    'type': unit_type,
                    'x': pos[0], 
                    'y': pos[1],
                    'index': i
                })
        
        initial_count = len(purchased_units)
        print(f"Stress test: Purchased {initial_count} units")
        
        # Run multiple short rounds rapidly
        for round_num in range(2, 8):  # Rounds 2-7
            with self.subTest(round=round_num):
                if self.game.is_game_over():
                    break
                    
                # Verify all units still exist
                current_count = len(self.game.owned_units)
                self.assertEqual(current_count, initial_count,
                               f"Unit count mismatch in stress round {round_num}: expected {initial_count}, got {current_count}")
                
                # Quick combat
                self.game.start_combat()
                
                # Very short combat to stress the transitions
                for i in range(50):  # Only 50 frames
                    if self.game.phase == GamePhase.SHOPPING:
                        break
                    self.game.update_combat(FRAME_TIME)
                
                # Force end
                if self.game.phase == GamePhase.COMBAT:
                    self.game.end_combat()
                
                # Check again after rapid transition
                final_count = len(self.game.owned_units)
                self.assertEqual(final_count, initial_count,
                               f"Units lost during rapid transition in round {round_num}")


class TestUnitReset(unittest.TestCase):
    """Test that unit reset method properly resets all fields."""
    
    def test_unit_reset_comprehensive(self):
        """Test that unit.reset() properly resets all fields, especially death timer."""
        from unit import Unit, UnitState
        from status_effect import PoisonEffect
        
        # Create a unit and mess up its state to simulate end-of-combat conditions
        unit = Unit("Test Unit", "test")
        
        # Simulate a unit that's in bad state at end of combat
        unit.hp = 10  # Damaged
        unit.mp = 20  # Used mana
        unit.target = unit  # Has a target
        unit.state = UnitState.ATTACKING  # In combat state
        unit.attack_timer = 5.0  # On cooldown
        
        # Simulate casting state
        from skill import Skill
        test_skill = Skill("Test Skill", "Test skill")
        unit.cast_skill = test_skill
        unit.cast_timer = 2.0
        unit.cast_time = 3.0
        
        # Simulate movement
        unit.move_timer = 1.5
        
        # Simulate visual effects (the critical bug!)
        unit.flash_timer = 0.5
        unit.flash_color = (255, 0, 0)
        unit.flash_duration = 1.0
        unit.bump_timer = 0.3
        unit.bump_direction = (1, 0)
        unit.death_timer = 2.0  # This was causing units to die next round!
        unit.cast_jump_timer = 0.2
        
        # Add a status effect
        poison = PoisonEffect(5.0)
        unit.status_effects.append(poison)
        
        # Add a spell 
        unit.spell = test_skill
        
        # Now reset the unit
        unit.reset()
        
        # Verify all fields are properly reset
        
        # Basic stats
        self.assertEqual(unit.hp, unit.max_hp, "HP not reset to max")
        # MP is no longer a unit property - it's on the spell
        self.assertEqual(len(unit.status_effects), 0, "Status effects not cleared")
        
        # Combat state
        self.assertIsNone(unit.target, "Target not cleared")
        self.assertEqual(unit.state, UnitState.IDLE, "State not reset to IDLE")
        self.assertEqual(unit.attack_timer, 0, "Attack timer not reset")
        
        # Casting state
        self.assertIsNone(unit.cast_skill, "Cast skill not cleared")
        self.assertEqual(unit.cast_timer, 0, "Cast timer not reset")
        self.assertEqual(unit.cast_time, 0, "Cast time not reset")
        
        # Movement state
        self.assertEqual(unit.move_timer, 0, "Move timer not reset")
        
        # Visual effects (THE CRITICAL BUG FIXES)
        self.assertEqual(unit.flash_timer, 0, "Flash timer not reset")
        self.assertIsNone(unit.flash_color, "Flash color not cleared")
        self.assertEqual(unit.flash_duration, 0, "Flash duration not reset")
        self.assertEqual(unit.bump_timer, 0, "Bump timer not reset")
        self.assertEqual(unit.bump_direction, (0, 0), "Bump direction not reset")
        self.assertEqual(unit.death_timer, 0, "DEATH TIMER NOT RESET - This was the main bug!")
        self.assertEqual(unit.cast_jump_timer, 0, "Cast jump timer not reset")
        
        # Spells no longer have cooldowns to reset
    
    def test_unit_death_timer_bug_scenario(self):
        """Test the specific death timer bug scenario."""
        from unit import Unit
        
        unit = Unit("Dying Unit", "test")
        
        # Simulate a unit that died at the end of combat
        unit.hp = 0  # Unit is dead
        unit.death_timer = 1.5  # Death animation in progress
        
        # This would cause the unit to continue dying next round
        self.assertFalse(unit.is_alive(), "Unit should be dead before reset")
        
        # Reset the unit (as happens between rounds)
        unit.reset()
        
        # After reset, unit should be fully alive and death timer cleared
        self.assertTrue(unit.is_alive(), "Unit should be alive after reset")
        self.assertEqual(unit.death_timer, 0, "Death timer should be cleared")
        self.assertEqual(unit.hp, unit.max_hp, "HP should be restored")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)