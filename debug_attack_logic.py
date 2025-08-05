#!/usr/bin/env python3
"""
Debug attack logic to see if units that should attack actually do.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import Game, GamePhase, GameMode
from content.units import create_unit, get_available_units
from content.items import generate_item_shop
from content.skills import create_skill, get_skill_cost
from content.units import get_unit_cost
from constants import FRAME_TIME

def main():
    print("=== Testing Attack Logic ===")
    
    # Set up game
    game = Game(GameMode.ASYNC)
    game.available_units = get_available_units()
    game.available_items = generate_item_shop()
    
    # Override create methods
    game.create_unit = create_unit
    game.create_skill = create_skill
    game.get_unit_cost = get_unit_cost
    game.get_skill_cost = get_skill_cost
    
    # Start first round
    game.start_new_round()
    
    # Purchase units and position them strategically
    game.purchase_unit("necromancer", 3, 4)  # Position where it should be able to attack range 4
    game.purchase_unit("pyromancer", 2, 5)   # Position where it should be able to attack range 5
    
    print(f"Purchased units at strategic positions")
    
    # Don't add skills first, let's see basic attack behavior
    for unit in game.owned_units:
        print(f"{unit.name}: attack_range={unit.attack_range}, position=({unit.x}, {unit.y})")
    
    # Start first combat
    print("\n=== FIRST COMBAT ===")
    game.start_combat()
    
    print("Enemy positions:")
    for enemy in game.board.enemy_units:
        print(f"{enemy.name}: position=({enemy.x}, {enemy.y})")
    
    # Calculate distances
    print("\nDistance analysis:")
    for unit in game.board.player_units:
        for enemy in game.board.enemy_units:
            distance = game.board.get_distance(unit, enemy)
            in_range = distance <= unit.attack_range
            print(f"{unit.name} to {enemy.name}: distance={distance}, in_range={in_range} (unit range={unit.attack_range})")
    
    # Run just a few frames to see initial behavior
    stuck_counter = {}
    for frame in range(100):
        if game.phase == GamePhase.SHOPPING:
            print(f"Combat ended at frame {frame}")
            break
        
        # Before update, check what units should be able to do
        for unit in game.board.player_units:
            if unit.is_alive() and unit.state.name == 'IDLE' and unit.attack_timer <= 0:
                nearest_enemy = game.board.get_nearest_enemy(unit)
                if nearest_enemy:
                    distance = game.board.get_distance(unit, nearest_enemy)
                    can_attack = unit.can_attack(nearest_enemy)
                    in_attack_range = distance <= unit.attack_range
                    
                    # Check if unit is stuck
                    if in_attack_range and not can_attack:
                        key = f"{unit.name}_stuck"
                        stuck_counter[key] = stuck_counter.get(key, 0) + 1
                        if stuck_counter[key] == 1:  # First time stuck
                            print(f"Frame {frame}: {unit.name} should be able to attack {nearest_enemy.name} (distance={distance}, range={unit.attack_range}) but can_attack={can_attack}")
                            print(f"  Unit state: {unit.state}, attack_timer={unit.attack_timer}, alive={unit.is_alive()}")
                            print(f"  Enemy alive: {nearest_enemy.is_alive()}")
        
        # Update combat
        game.update_combat(FRAME_TIME)
        
        # After update, log attacks
        for unit in game.board.player_units:
            if unit.is_alive() and unit.state.name == 'ATTACKING':
                print(f"Frame {frame}: {unit.name} ATTACKING")
    
    print(f"\nFirst combat analysis:")
    for key, count in stuck_counter.items():
        if count > 1:
            print(f"{key}: stuck for {count} frames")
    
    if game.is_game_over():
        print("Game over!")
        return
    
    # Force end combat
    if game.phase == GamePhase.COMBAT:
        game.end_combat()
    
    # Test second round
    print(f"\n=== SECOND ROUND ===")
    
    # Start second combat  
    game.start_combat()
    
    print("Enemy positions:")
    for enemy in game.board.enemy_units:
        print(f"{enemy.name}: position=({enemy.x}, {enemy.y})")
    
    # Calculate distances again
    print("\nDistance analysis:")
    for unit in game.board.player_units:
        for enemy in game.board.enemy_units:
            distance = game.board.get_distance(unit, enemy)
            in_range = distance <= unit.attack_range
            print(f"{unit.name} to {enemy.name}: distance={distance}, in_range={in_range} (unit range={unit.attack_range})")
    
    # Track second round behavior
    stuck_counter = {}
    attack_attempts = 0
    
    for frame in range(100):
        if game.phase == GamePhase.SHOPPING:
            print(f"Second combat ended at frame {frame}")
            break
        
        # Before update, check what units should be able to do
        for unit in game.board.player_units:
            if unit.is_alive() and unit.state.name == 'IDLE' and unit.attack_timer <= 0:
                nearest_enemy = game.board.get_nearest_enemy(unit)
                if nearest_enemy:
                    distance = game.board.get_distance(unit, nearest_enemy)
                    can_attack = unit.can_attack(nearest_enemy)
                    in_attack_range = distance <= unit.attack_range
                    
                    # Check if unit is stuck
                    if in_attack_range and not can_attack:
                        key = f"{unit.name}_stuck"
                        stuck_counter[key] = stuck_counter.get(key, 0) + 1
                        if stuck_counter[key] == 1:  # First time stuck
                            print(f"Frame {frame}: {unit.name} should be able to attack {nearest_enemy.name} (distance={distance}, range={unit.attack_range}) but can_attack={can_attack}")
        
        # Update combat
        game.update_combat(FRAME_TIME)
        
        # After update, log attacks
        for unit in game.board.player_units:
            if unit.is_alive() and unit.state.name == 'ATTACKING':
                attack_attempts += 1
                if attack_attempts <= 3:  # Only log first few attacks
                    print(f"Frame {frame}: {unit.name} ATTACKING")
    
    print(f"\nSecond combat analysis:")
    for key, count in stuck_counter.items():
        if count > 1:
            print(f"{key}: stuck for {count} frames")
    
    if attack_attempts == 0:
        print("*** BUG CONFIRMED: No attacks in second round! ***")
    else:
        print(f"Second round had {attack_attempts} attack attempts")

if __name__ == '__main__':
    main()