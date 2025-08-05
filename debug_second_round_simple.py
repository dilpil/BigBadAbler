#!/usr/bin/env python3
"""
Simple debug script to test the "units never act in 2nd combat round" bug.
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
    print("=== Testing 2nd Combat Round Bug (Simple) ===")
    
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
    
    # Purchase some units
    game.purchase_unit("paladin", 1, 1)
    game.purchase_unit("berserker", 2, 2)
    
    print(f"Purchased units: {len(game.owned_units)}")
    
    # Add skills to units
    for unit in game.owned_units:
        from content.skills import get_default_skill
        skill = get_default_skill(unit.unit_type)
        if skill:
            unit.add_skill(skill)
    
    # Run first combat quickly
    print("\n=== FIRST COMBAT ===")
    game.start_combat()
    
    # Run for limited time and then force end
    for i in range(200):
        if game.phase == GamePhase.SHOPPING:
            break
        game.update_combat(FRAME_TIME)
    
    if game.phase == GamePhase.COMBAT:
        game.end_combat()
    
    print(f"First combat ended, now in round {game.round}")
    
    if game.is_game_over():
        print("Game over!")
        return
    
    # Now test second round
    print(f"\n=== SECOND ROUND (Round {game.round}) ===")
    print(f"Player units: {len(game.owned_units)}")
    
    # Check unit states before second combat
    for unit in game.owned_units:
        print(f"Unit {unit.name}: HP={unit.hp}/{unit.max_hp}, state={unit.state}, attack_timer={unit.attack_timer:.2f}")
    
    # Start second combat  
    game.start_combat()
    print(f"Second combat started")
    
    # Track if units act in the first 100 frames
    actions_detected = False
    
    for frame in range(100):
        if game.phase == GamePhase.SHOPPING:
            print(f"Combat ended early at frame {frame}")
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
                if (unit.state != before['state'] or 
                    abs(unit.attack_timer - before['attack_timer']) > 0.01 or
                    unit.x != before['x'] or unit.y != before['y']):
                    actions_detected = True
                    print(f"Frame {frame}: {unit.name} acted (state: {before['state']} -> {unit.state}, pos: ({before['x']},{before['y']}) -> ({unit.x},{unit.y}))")
                    break  # Only print first action per frame
                unit_index += 1
    
    if not actions_detected:
        print("\n*** BUG CONFIRMED: Units never acted in second round! ***")
        
        # Debug: Check unit states in detail
        print("\nDetailed unit analysis:")
        for unit in game.board.player_units:
            if unit.is_alive():
                print(f"{unit.name}:")
                print(f"  Position: ({unit.x}, {unit.y})")
                print(f"  State: {unit.state}")
                print(f"  Attack timer: {unit.attack_timer}")
                print(f"  HP: {unit.hp}/{unit.max_hp}")
                print(f"  MP: {unit.mp}/{unit.max_mp}")
                print(f"  Target: {unit.target}")
                print(f"  Board reference: {unit.board is not None}")
                
                # Check if enemies exist
                enemies = game.board.enemy_units
                print(f"  Enemies visible: {len([e for e in enemies if e.is_alive()])}")
                if enemies:
                    nearest = game.board.get_nearest_enemy(unit)
                    if nearest:
                        distance = game.board.get_distance(unit, nearest)
                        print(f"  Nearest enemy: {nearest.name} at distance {distance}")
                        print(f"  Can attack nearest: {unit.can_attack(nearest)}")
                    else:
                        print(f"  No nearest enemy found")
    else:
        print(f"\nUnits acted normally in second round")

if __name__ == '__main__':
    main()