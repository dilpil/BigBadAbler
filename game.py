from enum import Enum
from typing import List, Optional
import random
from board import Board
from unit import Unit, UnitType
from constants import FRAME_TIME

class GamePhase(Enum):
    SHOPPING = "shopping"
    COMBAT = "combat"
    POST_COMBAT = "post_combat"

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
        self.post_combat_timer = 0
        self.post_combat_duration = 4.0
        self.combat_result = None  # "victory" or "defeat"
        
        # Track total gold earned for enemy team budget
        self.total_gold_earned = 0
        
        self.message_log = []
        
    def start_new_round(self):
        self.round += 1
        self.gold = 100
        self.total_gold_earned += 100  # Track total gold earned
        self.phase = GamePhase.SHOPPING
        self.combat_time = 0
        
        # Clear the board instead of recreating it
        self.board.clear()
        
        for unit in self.owned_units:
            unit.reset()
            self.board.add_unit(unit, unit.original_x, unit.original_y, "player")
            unit.board = self.board
                
        self.generate_enemy_team()
        self.position_enemy_units()  # Position enemies during shopping phase
        self.generate_item_shop()
        
        self.add_message(f"Round {self.round} - Shopping Phase")
    
    def generate_enemy_team(self):
        from content.unit_registry import create_unit, get_available_units
        from content.items import get_all_items, create_item
        import random
        
        # Enemy team gets a budget equal to total gold player has earned
        enemy_budget = self.total_gold_earned
        self.add_message(f"Enemy budget: {enemy_budget} gold")
        
        # At least half the budget must be spent on units
        min_unit_budget = enemy_budget // 2
        
        self.enemy_team = []
        remaining_budget = enemy_budget
        
        # Phase 1: Buy units (spend at least half the budget)
        unit_types = get_available_units()
        unit_cost = 50  # All units cost 50 gold
        
        # Keep buying units while we have budget and haven't reached the minimum spend or unit limit
        while len(self.enemy_team) < 6 and remaining_budget >= unit_cost:
            # If we've spent enough on units and have less than min budget left, stop buying units
            units_spent = (len(self.enemy_team) + 1) * unit_cost
            if units_spent > min_unit_budget and (enemy_budget - remaining_budget + unit_cost) >= min_unit_budget:
                # Check if we should stop buying units to save budget for items/passives
                if random.random() < 0.3:  # 30% chance to stop early if minimum is met
                    break
            
            unit_type = random.choice(unit_types)
            unit = create_unit(unit_type)
            if unit:
                self.enemy_team.append(unit)
                remaining_budget -= unit_cost
        
        # Phase 2: Buy passive skills and items with remaining budget
        all_items = get_all_items()
        
        for unit in self.enemy_team:
            # Try to buy passive skills
            available_passives = unit.get_available_passive_skills()
            if available_passives:
                # Try to buy 1-3 passive skills per unit
                num_passives_to_try = min(random.randint(1, 3), len(available_passives))
                random.shuffle(available_passives)
                
                for passive_name in available_passives[:num_passives_to_try]:
                    passive_cost = unit.get_passive_skill_cost(passive_name)
                    if remaining_budget >= passive_cost:
                        self._add_passive_skill_to_unit(unit, passive_name)
                        remaining_budget -= passive_cost
            
            # Try to buy items (max 3 per unit)
            num_items_to_try = min(random.randint(0, 3), 3 - len(unit.items))
            for _ in range(num_items_to_try):
                if remaining_budget <= 0:
                    break
                    
                item_name = random.choice(all_items)
                item = create_item(item_name)
                if item and remaining_budget >= item.cost:
                    unit.add_item(item)
                    remaining_budget -= item.cost
    
    def _add_passive_skill_to_unit(self, unit, skill_name):
        """Add a passive skill to a unit"""
        # Import the appropriate skill creation function based on unit type
        if unit.unit_type.value == "necromancer":
            from content.units.necromancer import create_necromancer_skill
            skill = create_necromancer_skill(skill_name)
        elif unit.unit_type.value == "paladin":
            from content.units.paladin import create_paladin_skill
            skill = create_paladin_skill(skill_name)
        elif unit.unit_type.value == "pyromancer":
            from content.units.pyromancer import create_pyromancer_skill
            skill = create_pyromancer_skill(skill_name)
        elif unit.unit_type.value == "berserker":
            from content.units.berserker import create_berserker_skill
            skill = create_berserker_skill(skill_name)
        else:
            skill = None
            
        if skill and skill.is_passive:
            unit.add_passive_skill(skill)
    
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
        
        # Enemy units are already positioned during shopping phase
        
        self.add_message("Combat Phase Started!")
    
    def start_combat_paused(self):
        """Start combat but immediately pause it."""
        if self.phase != GamePhase.SHOPPING:
            return
            
        self.phase = GamePhase.COMBAT
        self.combat_time = 0
        self.combat_frame = 0
        self.paused = True
        
        # Enemy units are already positioned during shopping phase
        
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
        if self.phase == GamePhase.COMBAT:
            # Don't update if paused
            if self.paused:
                return
                
            self.combat_time += dt
            self.combat_frame += 1
            
            # Let the board handle all combat updates
            self.board.update_combat(dt)
                
            if self.check_combat_end() or self.combat_time >= self.max_combat_time:
                self.start_post_combat()
        elif self.phase == GamePhase.POST_COMBAT:
            # Continue updating visual effects and animations during post-combat
            self.board.update_projectiles(dt)  # Some projectiles might still be in flight
            self.board.update_visual_effects(dt)
            self.board.text_floater_manager.update(dt)
            
            self.post_combat_timer += dt
            if self.post_combat_timer >= self.post_combat_duration:
                self.end_combat()
    
    def check_combat_end(self) -> bool:
        player_alive = any(unit.is_alive() for unit in self.board.player_units)
        enemy_alive = any(unit.is_alive() for unit in self.board.enemy_units)
        
        return not player_alive or not enemy_alive
    
    def start_post_combat(self):
        """Start the post-combat phase to show results"""
        self.phase = GamePhase.POST_COMBAT
        self.post_combat_timer = 0
        
        player_alive = any(unit.is_alive() for unit in self.board.player_units)
        enemy_alive = any(unit.is_alive() for unit in self.board.enemy_units)
        
        if player_alive and not enemy_alive:
            self.combat_result = "victory"
            self.player_wins += 1
            self.add_message("Victory!")
            if self.player_wins >= 20:
                self.add_message("You Win the Game!")
        else:
            self.combat_result = "defeat"
            self.player_lives -= 1
            self.add_message("Defeat!")
            if self.player_lives <= 0:
                self.add_message("Game Over!")
    
    def end_combat(self):
        """Actually end combat and start new round"""
        self.combat_result = None
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
        from skill_factory import create_skill
        return create_skill(skill_name)
    
    def add_message(self, message: str):
        self.message_log.append(message)
        if len(self.message_log) > 20:
            self.message_log.pop(0)
    
    def is_game_over(self) -> bool:
        return self.player_lives <= 0 or self.player_wins >= 20