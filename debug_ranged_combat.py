#!/usr/bin/env python3
"""
Debug ranged units in combat to see if they act properly.
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
    print("=== Testing Ranged Units Combat Behavior ===")
    
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
    print(f"Round {game.round} started")
    
    # Purchase ranged units (necromancer and pyromancer)
    game.purchase_unit("necromancer", 0, 4)  # Far left
    game.purchase_unit("pyromancer", 1, 5)   # Close to left
    
    print(f"Purchased ranged units: {len(game.owned_units)}")
    
    # Add skills to units
    for unit in game.owned_units:
        from content.skills import get_default_skill
        skill = get_default_skill(unit.unit_type)
        if skill:
            unit.add_skill(skill)
        print(f"{unit.name}: attack_range={unit.attack_range}, position=({unit.x}, {unit.y})")
    
    # Run first combat quickly
    print("\n=== FIRST COMBAT ===")
    game.start_combat()
    
    print("Enemy positions:")
    for enemy in game.board.enemy_units:
        print(f"{enemy.name}: position=({enemy.x}, {enemy.y})")
    
    # Run combat and track what happens
    actions_count = 0
    attack_count = 0
    move_count = 0
    cast_count = 0
    
    for frame in range(300):
        if game.phase == GamePhase.SHOPPING:
            print(f"Combat ended at frame {frame}")
            break
            
        # Store unit states before update
        unit_states_before = []
        for unit in game.board.player_units:
            if unit.is_alive():
                unit_states_before.append({
                    'name': unit.name,
                    'state': unit.state,
                    'attack_timer': unit.attack_timer,
                    'x': unit.x,
                    'y': unit.y
                })
        
        # Update combat
        game.update_combat(FRAME_TIME)
        
        # Check if units acted
        unit_index = 0
        for unit in game.board.player_units:
            if unit.is_alive() and unit_index < len(unit_states_before):
                before = unit_states_before[unit_index]
                
                # Check for state changes
                if unit.state != before['state']:
                    actions_count += 1
                    if unit.state.name == 'ATTACKING':
                        attack_count += 1
                        nearest_enemy = game.board.get_nearest_enemy(unit)
                        distance = game.board.get_distance(unit, nearest_enemy) if nearest_enemy else -1
                        print(f"Frame {frame}: {unit.name} ATTACKING (distance to nearest enemy: {distance})")
                    elif unit.state.name == 'WALKING':
                        move_count += 1
                        if frame < 50:  # Only log early movement
                            print(f"Frame {frame}: {unit.name} WALKING from ({before['x']},{before['y']}) to ({unit.x},{unit.y})")
                    elif unit.state.name == 'CASTING':
                        cast_count += 1
                        print(f"Frame {frame}: {unit.name} CASTING")
                
                # Check for position changes (without state change)
                elif unit.x != before['x'] or unit.y != before['y']:
                    if frame < 50:  # Only log early movement
                        print(f"Frame {frame}: {unit.name} moved from ({before['x']},{before['y']}) to ({unit.x},{unit.y})")
                
                unit_index += 1
        
        # Every 50 frames, show unit status
        if frame % 50 == 0 and frame > 0:
            print(f"\n--- Frame {frame} Status ---")
            for unit in game.board.player_units:
                if unit.is_alive():
                    nearest_enemy = game.board.get_nearest_enemy(unit)
                    distance = game.board.get_distance(unit, nearest_enemy) if nearest_enemy else -1
                    can_attack = unit.can_attack(nearest_enemy) if nearest_enemy else False
                    print(f"{unit.name}: pos=({unit.x},{unit.y}), state={unit.state.name}, attack_timer={unit.attack_timer:.2f}, distance_to_enemy={distance}, can_attack={can_attack}")
    
    print(f"\nFirst combat summary:")
    print(f"Total actions: {actions_count}")
    print(f"Attacks: {attack_count}")
    print(f"Moves: {move_count}")
    print(f"Casts: {cast_count}")
    
    if game.is_game_over():
        print("Game over!")
        return
    
    # Force end combat if it didn't end naturally
    if game.phase == GamePhase.COMBAT:
        game.end_combat()
    
    # Now test second round
    print(f"\n=== SECOND ROUND (Round {game.round}) ===")
    
    # Check unit states before second combat
    for unit in game.owned_units:
        print(f"Unit {unit.name}: HP={unit.hp}/{unit.max_hp}, pos=({unit.x},{unit.y}), state={unit.state}")
    
    # Start second combat  
    game.start_combat()
    print(f"Second combat started")
    
    print("Enemy positions:")
    for enemy in game.board.enemy_units:
        print(f"{enemy.name}: position=({enemy.x}, {enemy.y})")
    
    # Track second round
    actions_count = 0
    attack_count = 0
    move_count = 0
    cast_count = 0
    
    for frame in range(300):
        if game.phase == GamePhase.SHOPPING:
            print(f"Second combat ended at frame {frame}")
            break
            
        # Store unit states before update
        unit_states_before = []
        for unit in game.board.player_units:
            if unit.is_alive():
                unit_states_before.append({
                    'name': unit.name,
                    'state': unit.state,
                    'attack_timer': unit.attack_timer,
                    'x': unit.x,
                    'y': unit.y
                })
        
        # Update combat
        game.update_combat(FRAME_TIME)
        
        # Check if units acted
        unit_index = 0
        for unit in game.board.player_units:
            if unit.is_alive() and unit_index < len(unit_states_before):
                before = unit_states_before[unit_index]
                
                # Check for state changes
                if unit.state != before['state']:
                    actions_count += 1
                    if unit.state.name == 'ATTACKING':
                        attack_count += 1
                        nearest_enemy = game.board.get_nearest_enemy(unit)
                        distance = game.board.get_distance(unit, nearest_enemy) if nearest_enemy else -1
                        print(f"Frame {frame}: {unit.name} ATTACKING (distance to nearest enemy: {distance})")
                    elif unit.state.name == 'WALKING':
                        move_count += 1
                        if frame < 50:  # Only log early movement
                            print(f"Frame {frame}: {unit.name} WALKING from ({before['x']},{before['y']}) to ({unit.x},{unit.y})")
                    elif unit.state.name == 'CASTING':
                        cast_count += 1
                        print(f"Frame {frame}: {unit.name} CASTING")
                
                unit_index += 1
        
        # Every 50 frames, show unit status
        if frame % 50 == 0 and frame > 0:
            print(f"\n--- Frame {frame} Status ---")
            for unit in game.board.player_units:
                if unit.is_alive():
                    nearest_enemy = game.board.get_nearest_enemy(unit)
                    distance = game.board.get_distance(unit, nearest_enemy) if nearest_enemy else -1
                    can_attack = unit.can_attack(nearest_enemy) if nearest_enemy else False
                    in_attack_range = distance <= unit.attack_range if nearest_enemy else False
                    print(f"{unit.name}: pos=({unit.x},{unit.y}), state={unit.state.name}, attack_timer={unit.attack_timer:.2f}, distance_to_enemy={distance}, in_range={in_attack_range}, can_attack={can_attack}")
    
    print(f"\nSecond combat summary:")
    print(f"Total actions: {actions_count}")
    print(f"Attacks: {attack_count}")
    print(f"Moves: {move_count}")
    print(f"Casts: {cast_count}")
    
    if actions_count == 0:
        print("\n*** BUG CONFIRMED: Units never acted in second round! ***")
    else:
        print(f"\nUnits acted normally in second round")

if __name__ == '__main__':
    main()