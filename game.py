from enum import Enum
from typing import List, Optional
import random
from board import Board
from unit import Unit, UnitType
from constants import FRAME_TIME

class GamePhase(Enum):
    SHOPPING = "shopping"
    COMBAT = "combat"

class GameMode(Enum):
    ASYNC = "async"
    REALTIME = "realtime"
    TOURNAMENT = "tournament"

class Game:
    def __init__(self, mode: GameMode = GameMode.ASYNC):
        self.mode = mode
        self.round = 0
        self.player_lives = 5
        self.player_wins = 0
        self.gold = 100
        
        self.phase = GamePhase.SHOPPING
        self.board = Board()
        self.board.game = self
        
        self.owned_units = []
        self.enemy_team = []
        self.item_shop = []
        
        self.available_units = []
        self.available_items = []
        
        self.combat_time = 0
        self.max_combat_time = 60.0
        self.combat_frame = 0
        self.paused = False
        
        self.message_log = []
        
    def start_new_round(self):
        self.round += 1
        self.gold = 100
        self.phase = GamePhase.SHOPPING
        self.combat_time = 0
        
        # Clear the board instead of recreating it
        self.board.clear()
        
        for unit in self.owned_units:
            unit.reset()
            self.board.add_unit(unit, unit.original_x, unit.original_y, "player")
            unit.board = self.board
                
        self.generate_enemy_team()
        self.generate_item_shop()
        
        self.add_message(f"Round {self.round} - Shopping Phase")
    
    def generate_enemy_team(self):
        from content.unit_registry import create_unit, get_available_units
        import random
        
        num_enemies = min(self.round // 3 + 2, 6)
        unit_types = get_available_units()
        
        self.enemy_team = []
        for i in range(num_enemies):
            unit_type = random.choice(unit_types)
            unit = create_unit(unit_type)
            if unit:
                # Unit already has default skill set on creation
                self.enemy_team.append(unit)
    
    def generate_item_shop(self):
        from content.items import generate_item_shop
        self.item_shop = generate_item_shop(10)
    
    def purchase_unit(self, unit_type: UnitType, x: int, y: int) -> bool:
        cost = self.get_unit_cost(unit_type)
        if self.gold < cost:
            return False
            
        unit = self.create_unit(unit_type)
        if not unit:
            return False
            
        if self.board.add_unit(unit, x, y, "player"):
            self.gold -= cost
            self.owned_units.append(unit)
            unit.board = self.board
            unit.original_x = x
            unit.original_y = y
            self.add_message(f"Purchased {unit.name} for {cost} gold")
            return True
            
        return False
    
    def purchase_skill(self, unit: Unit, skill_name: str) -> bool:
        cost = self.get_skill_cost(skill_name)
        if self.gold < cost:
            return False
            
        if unit.spell:
            return False
            
        skill = self.create_skill(skill_name)
        if not skill:
            return False
            
        if unit.set_spell(skill):
            self.gold -= cost
            self.add_message(f"Purchased {skill.name} for {unit.name} for {cost} gold")
            return True
            
        return False
    
    def purchase_passive_skill(self, unit: Unit, skill_name: str) -> bool:
        """Purchase a passive skill for a unit"""
        cost = unit.get_passive_skill_cost(skill_name)
        if self.gold < cost:
            return False
            
        # Check if unit already has this passive skill
        for passive in unit.passive_skills:
            if passive.name.lower().replace(" ", "_") == skill_name.lower():
                return False
                
        skill = self.create_skill(skill_name)
        if not skill:
            return False
            
        if unit.add_passive_skill(skill):
            self.gold -= cost
            self.add_message(f"Purchased {skill.name} for {unit.name} for {cost} gold")
            return True
            
        return False
    
    def purchase_item(self, item_name: str, unit: Unit) -> bool:
        item = None
        for shop_item in self.item_shop:
            if shop_item.name == item_name:
                item = shop_item
                break
                
        if not item:
            return False
            
        if self.gold < item.cost:
            return False
            
        if len(unit.items) >= 3:
            return False
            
        if unit.add_item(item):
            self.gold -= item.cost
            self.item_shop.remove(item)
            self.add_message(f"Purchased {item.name} for {unit.name} for {item.cost} gold")
            return True
            
        return False
    
    def start_combat(self):
        if self.phase != GamePhase.SHOPPING:
            return
            
        self.phase = GamePhase.COMBAT
        self.combat_time = 0
        self.combat_frame = 0
        
        self.position_enemy_units()
        
        self.add_message("Combat Phase Started!")
    
    def start_combat_paused(self):
        """Start combat but immediately pause it."""
        if self.phase != GamePhase.SHOPPING:
            return
            
        self.phase = GamePhase.COMBAT
        self.combat_time = 0
        self.combat_frame = 0
        self.paused = True
        
        self.position_enemy_units()
        
        self.add_message("Combat Phase Started (Paused)")
    
    def toggle_pause(self):
        """Toggle pause state during combat."""
        if self.phase == GamePhase.COMBAT:
            self.paused = not self.paused
            if self.paused:
                self.add_message("Combat Paused")
            else:
                self.add_message("Combat Resumed")
    
    def advance_one_frame(self):
        """Advance combat by one frame while paused."""
        if self.phase == GamePhase.COMBAT and self.paused:
            # Temporarily unpause for one frame
            self.paused = False
            self.update_combat(FRAME_TIME)  # Advance by one frame
            self.paused = True
    
    def position_enemy_units(self):
        for i, unit in enumerate(self.enemy_team):
            x = 8 + (i % 2)
            y = 3 + (i // 2) * 2
            self.board.add_unit(unit, x, y, "enemy")
            unit.board = self.board
    
    def update_combat(self, dt: float):
        if self.phase != GamePhase.COMBAT:
            return
            
        # Don't update if paused
        if self.paused:
            return
            
        self.combat_time += dt
        self.combat_frame += 1
        
        # Let the board handle all combat updates
        self.board.update_combat(dt)
            
        if self.check_combat_end() or self.combat_time >= self.max_combat_time:
            self.end_combat()
    
    def check_combat_end(self) -> bool:
        player_alive = any(unit.is_alive() for unit in self.board.player_units)
        enemy_alive = any(unit.is_alive() for unit in self.board.enemy_units)
        
        return not player_alive or not enemy_alive
    
    def end_combat(self):
        player_alive = any(unit.is_alive() for unit in self.board.player_units)
        enemy_alive = any(unit.is_alive() for unit in self.board.enemy_units)
        
        if player_alive and not enemy_alive:
            self.player_wins += 1
            self.add_message("Victory!")
            if self.player_wins >= 20:
                self.add_message("You Win the Game!")
        else:
            self.player_lives -= 1
            self.add_message("Defeat!")
            if self.player_lives <= 0:
                self.add_message("Game Over!")
                
        self.start_new_round()
    
    def get_unit_cost(self, unit_type: UnitType) -> int:
        from content.unit_registry import get_unit_cost
        return get_unit_cost(unit_type)
    
    def get_skill_cost(self, skill_name: str) -> int:
        return 25
    
    def create_unit(self, unit_type: UnitType) -> Optional[Unit]:
        from content.unit_registry import create_unit
        return create_unit(unit_type)
    
    def create_skill(self, skill_name: str):
        from content.skills import create_skill
        return create_skill(skill_name)
    
    def add_message(self, message: str):
        self.message_log.append(message)
        if len(self.message_log) > 20:
            self.message_log.pop(0)
    
    def is_game_over(self) -> bool:
        return self.player_lives <= 0 or self.player_wins >= 20