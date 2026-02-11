from typing import List, Optional
from unit import Unit

class Team:
    """Represents a team of units with their augments and items"""
    
    def __init__(self, name: str, board=None):
        self.name = name  # "player" or "enemy"
        self.board = board  # Reference to the game board
        
        # Units and augments
        self.units: List[Unit] = []
        self.augments = []  # All augments owned by this team
        self.passive_augments = []  # Just passive augments for combat effects
        self.unequipped_items = []  # Items not currently equipped to units

        # Team stats
        self.units_purchased = 0  # Track for escalating unit costs
        
    def add_unit(self, unit: Unit, x: int = None, y: int = None) -> bool:
        """Add a unit to the team and optionally place it on the board"""
        self.units.append(unit)
        unit.team_obj = self  # Reference back to team

        # Try to place on board if coordinates provided
        if self.board and x is not None and y is not None:
            if self.board.add_unit(unit, x, y, self.name):
                unit.original_x = x
                unit.original_y = y
            else:
                # Couldn't place on board, remove from team
                self.units.remove(unit)
                return False

        # Apply all passive augment buffs to the new unit
        for augment in self.passive_augments:
            if hasattr(augment, 'apply_to_unit'):
                augment.apply_to_unit(unit)

        return True
    
    def remove_unit(self, unit: Unit):
        """Remove a unit from the team"""
        if unit in self.units:
            self.units.remove(unit)
            unit.team_obj = None
    
    def add_augment(self, augment):
        """Add an augment to the team"""
        augment.team = self
        self.augments.append(augment)
        
        # Also track passive augments separately for combat effects
        from augment import PassiveAugment
        if isinstance(augment, PassiveAugment):
            self.passive_augments.append(augment)
    
    def get_unit_cost(self) -> int:
        """Get the cost for the next unit purchase (escalating)"""
        return 40 + (self.units_purchased * 20)
    
    def get_passive_cost(self, unit: Unit) -> int:
        """Get the cost for the next passive skill for a unit (escalating)"""
        return 30 + (len(unit.passive_skills) * 20)
    
    def find_empty_position(self) -> Optional[tuple]:
        """Find an empty position on the team's side of the board"""
        if not self.board:
            return None
            
        # Player units go on left (x=0-3), enemy on right (x=4-7)
        if self.name == "player":
            x_range = range(4)
        else:
            x_range = range(4, 8)
            
        for x in x_range:
            for y in range(8):
                if not self.board.get_unit_at(x, y):
                    return (x, y)
        return None
    
    def reset_for_combat(self):
        """Reset all units for combat"""
        for unit in self.units:
            unit.reset()
            if self.board and hasattr(unit, 'original_x') and hasattr(unit, 'original_y'):
                self.board.add_unit(unit, unit.original_x, unit.original_y, self.name)

        # Reapply augment buffs after reset (since reset clears status effects)
        for unit in self.units:
            for augment in self.passive_augments:
                if hasattr(augment, 'apply_to_unit'):
                    augment.apply_to_unit(unit)
    
    def clear(self):
        """Clear all units and augments (for enemy team regeneration)"""
        self.units.clear()
        self.augments.clear()
        self.passive_augments.clear()
        self.unequipped_items.clear()
        self.units_purchased = 0
    
    def update(self, dt: float):
        """Update all passive augments during combat"""
        for augment in self.passive_augments:
            if hasattr(augment, 'on_frame'):
                augment.on_frame(dt)

    def on_battle_start(self):
        """Called at the start of battle - activate passive augments"""
        for augment in self.passive_augments:
            if hasattr(augment, 'on_battle_start'):
                augment.on_battle_start()
    
    def on_round_end(self, game=None):
        """Called at the end of round - trigger passive augment effects"""
        for augment in self.passive_augments:
            if hasattr(augment, 'on_round_end'):
                # Try to pass game object if augment accepts it
                if game:
                    try:
                        augment.on_round_end(game)
                    except TypeError:
                        # Augment doesn't accept game parameter, call without it
                        augment.on_round_end()
                else:
                    augment.on_round_end()
    
    def buy_random_unit(self, remaining_budget: int, game=None) -> int:
        """Try to buy a random unit for the enemy team. Returns cost spent (0 if failed)."""
        from content.unit_registry import create_unit, get_available_units
        import random
        
        # Check if we can afford a unit
        unit_cost = self.get_unit_cost()
        if remaining_budget < unit_cost:
            return 0
        
        # Check if we have space for a unit
        position = self.find_empty_position()
        if not position:
            return 0
        
        # Try to create and add a random unit
        unit_types = get_available_units()
        if not unit_types:
            return 0
            
        unit_type = random.choice(unit_types)
        unit = create_unit(unit_type)
        
        if unit and self.add_unit(unit, position[0], position[1]):
            self.units_purchased += 1
            if game:
                game.add_message(f"Enemy bought {unit.name} for {unit_cost} gold")
            return unit_cost
        
        return 0
    
    def buy_random_passive(self, remaining_budget: int, game=None) -> int:
        """Try to buy a random passive skill for a random unit. Returns cost spent (0 if failed)."""
        import random
        
        # Find eligible units (units with < 5 passive skills)
        eligible_units = [unit for unit in self.units if len(unit.passive_skills) < 5]
        if not eligible_units:
            return 0
        
        # Pick a random unit
        unit = random.choice(eligible_units)
        skill_cost = self.get_passive_cost(unit)
        
        # Check if we can afford a passive
        if remaining_budget < skill_cost:
            return 0
        
        # Get available passive skills for this unit
        if not hasattr(unit, 'get_available_passive_skills'):
            return 0
            
        available_passives = unit.get_available_passive_skills()
        if not available_passives:
            return 0
        
        # Filter out skills the unit already has
        eligible_passives = []
        for passive_skill in available_passives:
            skill_name = passive_skill.value if hasattr(passive_skill, 'value') else str(passive_skill)
            has_skill = any(existing.name.lower().replace(" ", "_") == skill_name.lower().replace(" ", "_")
                          for existing in unit.passive_skills)
            if not has_skill:
                eligible_passives.append(passive_skill)
        
        if not eligible_passives:
            return 0
        
        # Buy a random passive skill
        skill_to_buy = random.choice(eligible_passives)
        from skill_factory import create_skill
        skill = create_skill(skill_to_buy)
        
        if skill and unit.add_passive_skill(skill):
            if game:
                game.add_message(f"Enemy bought {skill.name} for {unit.name} for {skill_cost} gold")
            return skill_cost
        
        return 0
    
    def buy_random_augment(self, remaining_budget: int, game=None) -> int:
        """Try to buy a random augment from the pool. Returns cost spent (0 if failed)."""
        import random
        
        # Check if we have augments in the pool
        if not hasattr(self, 'enemy_augment_pool') or not self.enemy_augment_pool:
            return 0
        
        # Find affordable augments we haven't bought yet
        available_augments = [aug for aug in self.enemy_augment_pool 
                            if aug.cost <= remaining_budget and aug not in self.augments]
        
        if not available_augments:
            return 0
        
        # Pick a random augment
        augment = random.choice(available_augments)
        
        # 70% chance to buy (for enemy balance)
        if random.random() > 0.7:
            return 0
        
        # Try to buy the augment
        augment.team = self
        if augment.on_buy(self):
            self.add_augment(augment)
            if game:
                game.add_message(f"Enemy bought {augment.name} for {augment.cost} gold")
            return augment.cost
        
        return 0
    
    def equip_items_randomly(self):
        """Randomly equip unequipped items to units with available slots."""
        import random
        
        for item in self.unequipped_items[:]:  # Use slice copy to avoid modification during iteration
            available_units = [unit for unit in self.units if len(unit.items) < 3]
            if available_units:
                unit = random.choice(available_units)
                if unit.add_item(item):
                    self.unequipped_items.remove(item)
    
    def generate_enemy_team(self, budget: int = 120, game=None):
        """Generate an enemy team by randomly buying units, passives, and augments until budget is exhausted."""
        from content.augments import generate_augment_shop_legacy
        import random
        
        if self.name != "enemy":
            return  # Only generate for enemy teams
        
        if game:
            game.add_message(f"Enemy budget: {budget} gold")
        
        # Clear enemy team completely
        self.clear()
        
        # Generate augment pool once for the enemy to choose from
        self.enemy_augment_pool = generate_augment_shop_legacy(20)
        random.shuffle(self.enemy_augment_pool)
        
        remaining_budget = budget
        attempts = 0
        max_attempts = 200
        
        # Keep buying randomly until budget < 50 or max attempts reached
        while remaining_budget >= 50 and attempts < max_attempts:
            attempts += 1
            
            # Randomly choose what to buy
            # Weighted: 50% units, 25% passives, 25% augments
            choice = random.choices(
                ['unit', 'passive', 'augment'],
                weights=[0.5, 0.25, 0.25],
                k=1
            )[0]
            
            cost_spent = 0
            
            if choice == 'unit':
                cost_spent = self.buy_random_unit(remaining_budget, game)
            elif choice == 'passive':
                # Only try to buy passives if we have units
                if self.units:
                    cost_spent = self.buy_random_passive(remaining_budget, game)
            elif choice == 'augment':
                cost_spent = self.buy_random_augment(remaining_budget, game)
            
            remaining_budget -= cost_spent
            
            # If we haven't spent anything in 10 attempts, try to force a unit purchase
            if attempts % 10 == 0 and cost_spent == 0:
                # Check if we can afford the cheapest option (base unit)
                if remaining_budget >= 40 and not self.units:
                    # Force try to buy a unit
                    cost_spent = self.buy_random_unit(remaining_budget, game)
                    remaining_budget -= cost_spent
        
        # Equip any unequipped items randomly
        self.equip_items_randomly()
        
        # Report final spending
        total_spent = budget - remaining_budget
        if game:
            if attempts >= max_attempts:
                game.add_message(f"Enemy stopped after {max_attempts} attempts")
            game.add_message(f"Enemy spent {total_spent} gold total, {remaining_budget} gold left over")