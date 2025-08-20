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
        self.gold = 200
        
        self.phase = GamePhase.SHOPPING
        self.board = Board()
        self.board.game = self
        
        self.owned_units = []
        self.enemy_team = []
        self.augment_shop = []
        self.owned_augments = []  # ALL purchased augments
        self.passive_augments = []  # Just passive augments for combat effects
        self.unequipped_items = []
        
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
        # Track units purchased for escalating costs
        self.units_purchased_this_game = 0
        
        self.message_log = []
        
    def start_new_round(self):
        self.round += 1
        gold_gained = 200  # Each round gets 200 gold
        self.gold = gold_gained
        self.total_gold_earned += gold_gained  # Track total gold earned
        self.phase = GamePhase.SHOPPING
        self.combat_time = 0
        
        # Clear the board instead of recreating it
        self.board.clear()
        
        for unit in self.owned_units:
            unit.reset()
            self.board.add_unit(unit, unit.original_x, unit.original_y, "player")
                
        self.generate_enemy_team()
        self.position_enemy_units()  # Position enemies during shopping phase
        self.generate_augment_shop()
        
        self.add_message(f"Round {self.round} - Shopping Phase")
    
    def generate_enemy_team(self):
        from content.augments import generate_augment_shop
        import random
        
        # Enemy gets same budget as player per round (200 gold)
        enemy_budget = 200
        self.add_message(f"Enemy budget: {enemy_budget} gold")
        
        # Clear enemy team
        self.enemy_team = []
        
        # Create a temporary enemy game state to use augment purchasing
        enemy_augments = generate_augment_shop(20)  # Larger pool for enemy to choose from
        remaining_budget = enemy_budget
        enemy_owned_augments = []
        enemy_unequipped_items = []
        
        # Randomly purchase augments until budget is exhausted
        random.shuffle(enemy_augments)  # Randomize order
        
        for augment in enemy_augments:
            if remaining_budget >= augment.cost:
                # 70% chance to buy each affordable augment (makes enemy slightly less optimal than player)
                if random.random() < 0.7:
                    # Simulate purchasing the augment
                    if augment.on_buy(self):
                        remaining_budget -= augment.cost
                        enemy_owned_augments.append(augment)
                        
                        # For ItemAugments, move items from unequipped to a separate enemy pool
                        from augment import ItemAugment
                        if isinstance(augment, ItemAugment) and hasattr(augment, 'item'):
                            if augment.item in self.unequipped_items:
                                self.unequipped_items.remove(augment.item)
                                enemy_unequipped_items.append(augment.item)
        
        # Equip items to enemy units randomly
        for item in enemy_unequipped_items:
            available_units = [unit for unit in self.enemy_team if len(unit.items) < 3]
            if available_units:
                unit = random.choice(available_units)
                unit.add_item(item)
        
        self.add_message(f"Enemy spent {enemy_budget - remaining_budget} gold, {remaining_budget} left over")
    
    def generate_augment_shop(self):
        from content.augments import generate_augment_shop
        self.augment_shop = generate_augment_shop(5)
    
    def purchase_unit(self, unit_type: UnitType, x: int, y: int) -> bool:
        cost = self.get_unit_cost(unit_type)
        if self.gold < cost:
            return False
            
        unit = self.create_unit(unit_type)
        if not unit:
            return False
            
        if self.board.add_unit(unit, x, y, "player"):
            self.gold -= cost
            self.units_purchased_this_game += 1  # Track for escalating costs
            self.owned_units.append(unit)
            unit.original_x = x
            unit.original_y = y
            self.add_message(f"Purchased {unit.name} for {cost} gold")
            # Play purchase sound
            if hasattr(self, 'ui') and self.ui:
                self.ui.play_sound('buy')
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
            # Play purchase sound
            if hasattr(self, 'ui') and self.ui:
                self.ui.play_sound('buy')
            return True
            
        return False
    
    def purchase_passive_skill(self, unit: Unit, skill_name: str) -> bool:
        """Purchase a passive skill for a unit"""
        # Escalating cost: 30 + 20 for each existing passive
        cost = 30 + (len(unit.passive_skills) * 20)
        if self.gold < cost:
            return False
            
        # Check if unit already has this passive skill (handle both string and enum)
        for passive in unit.passive_skills:
            if hasattr(passive, 'skill_enum') and passive.skill_enum == skill_name:
                return False
            elif hasattr(skill_name, 'value') and passive.name.lower().replace(" ", "_") == skill_name.value:
                return False
            elif isinstance(skill_name, str) and passive.name.lower().replace(" ", "_") == skill_name.lower():
                return False
                
        skill = self.create_skill(skill_name)
        if not skill:
            return False
            
        if unit.add_passive_skill(skill):
            self.gold -= cost
            self.add_message(f"Purchased {skill.name} for {unit.name} for {cost} gold")
            # Play purchase sound
            if hasattr(self, 'ui') and self.ui:
                self.ui.play_sound('buy')
            return True
            
        return False
    
    def purchase_augment(self, augment_index: int) -> bool:
        """Purchase an augment from the shop"""
        if augment_index >= len(self.augment_shop):
            return False
            
        augment = self.augment_shop[augment_index]
        
        if self.gold < augment.cost:
            return False
            
        # Try to buy the augment
        if augment.on_buy(self):
            self.gold -= augment.cost
            self.augment_shop.pop(augment_index)
            self.add_message(f"Purchased {augment.name} for {augment.cost} gold")
            # Play purchase sound
            if hasattr(self, 'ui') and self.ui:
                self.ui.play_sound('buy')
            return True
            
        return False
    
    def purchase_item(self, item_name: str, unit: Unit) -> bool:
        """Legacy method for direct item purchases (kept for compatibility)"""
        # Check unequipped items first
        item = None
        for unequipped_item in self.unequipped_items:
            if unequipped_item.name == item_name:
                item = unequipped_item
                break
                
        if not item:
            return False
            
        if len(unit.items) >= 3:
            return False
            
        if unit.add_item(item):
            self.unequipped_items.remove(item)
            self.add_message(f"Equipped {item.name} to {unit.name}")
            return True
            
        return False
    
    def start_combat(self):
        if self.phase != GamePhase.SHOPPING:
            return
            
        self.phase = GamePhase.COMBAT
        self.combat_time = 0
        self.combat_frame = 0
        
        # Trigger passive augments' battle start effects
        for augment in self.passive_augments:
            if hasattr(augment, 'on_battle_start'):
                augment.on_battle_start()
        
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
            # Position enemies on the right side of the 8x8 board (x=6-7)
            x = 6 + (i % 2)
            y = 1 + (i // 2)
            # Ensure we don't exceed board boundaries
            if y >= 8:
                y = 7
            self.board.add_unit(unit, x, y, "enemy")
    
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
        # Trigger passive augments' round end effects
        for augment in self.passive_augments:
            if hasattr(augment, 'on_round_end'):
                augment.on_round_end()
        
        self.combat_result = None
        self.start_new_round()
    
    def get_unit_cost(self, unit_type: UnitType) -> int:
        # Escalating costs: 40, 60, 80, 100, etc.
        return 40 + (self.units_purchased_this_game * 20)
    
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