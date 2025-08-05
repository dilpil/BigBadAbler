#!/usr/bin/env python3
"""
Debug script to test the "units never act in 2nd combat round" bug.
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
    print("=== Testing 2nd Combat Round Bug ===")
    
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
    game.purchase_unit("necromancer", 1, 1)
    game.purchase_unit("paladin", 2, 2)
    
    print(f"Purchased units: {len(game.owned_units)}")
    print(f"Player units on board: {len(game.board.player_units)}")
    
    # Add skills to units
    for unit in game.owned_units:
        from content.skills import get_default_skill
        skill = get_default_skill(unit.unit_type)
        if skill:
            unit.add_skill(skill)
    
    # Start first combat
    print("\n=== FIRST COMBAT ===")
    game.start_combat()
    print(f"Combat started - Player units: {len(game.board.player_units)}, Enemy units: {len(game.board.enemy_units)}")
    
    # Track unit actions in first combat
    frame_count = 0
    actions_this_round = 0
    max_frames = 300
    
    while game.phase == GamePhase.COMBAT and frame_count < max_frames:
        # Before updating, check if any units are about to act
        for unit in game.board.player_units:
            if unit.is_alive():
                old_state = unit.state
                old_attack_timer = unit.attack_timer
                old_cast_timer = unit.cast_timer
                
        game.update_combat(FRAME_TIME)
        
        # After updating, check if units acted
        for unit in game.board.player_units:
            if unit.is_alive():
                if (unit.state != old_state or 
                    unit.attack_timer != old_attack_timer or 
                    unit.cast_timer != old_cast_timer):
                    actions_this_round += 1
                    print(f"Frame {frame_count}: {unit.name} acted (state: {unit.state}, attack_timer: {unit.attack_timer:.2f})")
        
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Frame {frame_count}: Player units alive: {sum(1 for u in game.board.player_units if u.is_alive())}, Enemy units alive: {sum(1 for u in game.board.enemy_units if u.is_alive())}")
    
    print(f"First combat ended after {frame_count} frames with {actions_this_round} unit actions")
    print(f"Final phase: {game.phase}")
    
    if game.is_game_over():
        print("Game over!")
        return
    
    # Now test second round
    print(f"\n=== SECOND ROUND ===")
    print(f"Round {game.round} started")
    print(f"Player units: {len(game.owned_units)}")
    print(f"Player units on board: {len(game.board.player_units)}")
    
    # Check unit states before second combat
    for unit in game.owned_units:
        print(f"Unit {unit.name}: HP={unit.hp}/{unit.max_hp}, state={unit.state}, attack_timer={unit.attack_timer:.2f}")
    
    # Start second combat  
    game.start_combat()
    print(f"Second combat started - Player units: {len(game.board.player_units)}, Enemy units: {len(game.board.enemy_units)}")
    
    # Track unit actions in second combat
    frame_count = 0
    actions_this_round = 0
    
    while game.phase == GamePhase.COMBAT and frame_count < max_frames:
        # Before updating, check unit states
        unit_states_before = []
        for unit in game.board.player_units:
            if unit.is_alive():
                unit_states_before.append({
                    'name': unit.name,
                    'state': unit.state,
                    'attack_timer': unit.attack_timer,
                    'cast_timer': unit.cast_timer,
                    'hp': unit.hp,
                    'mp': unit.mp
                })
                
        game.update_combat(FRAME_TIME)
        
        # After updating, check if units acted
        unit_index = 0
        for unit in game.board.player_units:
            if unit.is_alive() and unit_index < len(unit_states_before):
                before = unit_states_before[unit_index]
                if (unit.state != before['state'] or 
                    unit.attack_timer != before['attack_timer'] or 
                    unit.cast_timer != before['cast_timer']):
                    actions_this_round += 1
                    print(f"Frame {frame_count}: {unit.name} acted (state: {before['state']} -> {unit.state})")
                unit_index += 1
        
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Frame {frame_count}: Player units alive: {sum(1 for u in game.board.player_units if u.is_alive())}, Enemy units alive: {sum(1 for u in game.board.enemy_units if u.is_alive())}")
            # Print detailed unit states every 100 frames
            for unit in game.board.player_units:
                if unit.is_alive():
                    print(f"  {unit.name}: state={unit.state}, attack_timer={unit.attack_timer:.2f}, target={unit.target.name if unit.target else None}")
    
    print(f"Second combat ended after {frame_count} frames with {actions_this_round} unit actions")
    
    if actions_this_round == 0:
        print("\n*** BUG CONFIRMED: Units never acted in second round! ***")
    else:
        print(f"\nUnits acted normally in second round ({actions_this_round} actions)")

if __name__ == '__main__':
    main()