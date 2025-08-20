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
                return True
            else:
                # Couldn't place on board, remove from team
                self.units.remove(unit)
                return False
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
    
    def clear(self):
        """Clear all units and augments (for enemy team regeneration)"""
        self.units.clear()
        self.augments.clear()
        self.passive_augments.clear()
        self.unequipped_items.clear()
        self.units_purchased = 0
    
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
    
    def generate_enemy_team(self, budget: int = 120, game=None):
        """Generate an enemy team with random allocation: 50%+ units, remainder split between upgrades and augments"""
        from content.augments import generate_augment_shop
        from augment import ItemAugment, UnitAugment, PassiveAugment
        from content.unit_registry import create_unit, get_available_units
        import random
        
        if self.name != "enemy":
            return  # Only generate for enemy teams
        
        if game:
            game.add_message(f"Enemy budget: {budget} gold")
        
        # Clear enemy team completely
        self.clear()
        
        # Randomly allocate budget percentages
        # Units get 50-80% of budget
        unit_percentage = random.uniform(0.5, 0.8)
        unit_budget = int(budget * unit_percentage)
        
        # Split remainder between upgrades and augments
        remaining_percentage = 1.0 - unit_percentage
        upgrade_percentage = random.uniform(0, remaining_percentage)
        augment_percentage = remaining_percentage - upgrade_percentage
        
        upgrade_budget = int(budget * upgrade_percentage)
        augment_budget = int(budget * augment_percentage)

        if game:
            game.add_message(f"Enemy allocation: {unit_percentage:.1%} units ({unit_budget}g), {upgrade_percentage:.1%} upgrades ({upgrade_budget}g), {augment_percentage:.1%} augments ({augment_budget}g)")
        
        # Phase 1: Buy units with unit budget
        unit_types = get_available_units()
        remaining_unit_budget = unit_budget
        
        while remaining_unit_budget >= 40 and unit_types:  # 40 is base unit cost
            unit_type = random.choice(unit_types)
            unit = create_unit(unit_type)
            if unit:
                unit_cost = self.get_unit_cost()
                if remaining_unit_budget >= unit_cost:
                    position = self.find_empty_position()
                    if position and self.add_unit(unit, position[0], position[1]):
                        remaining_unit_budget -= unit_cost
                        self.units_purchased += 1
                        if game:
                            game.add_message(f"Enemy bought {unit.name} for {unit_cost} gold")
                    else:
                        break  # No more space for units
                else:
                    break  # Can't afford more units
            else:
                break  # Failed to create unit
        
        # Phase 2: Buy upgrades (passive skills) with upgrade budget
        remaining_upgrade_budget = upgrade_budget + remaining_unit_budget
        
        while remaining_upgrade_budget >= 30 and self.units:  # 30 is base passive cost
            # Pick a random unit that can still get upgrades
            eligible_units = [unit for unit in self.units if len(unit.passive_skills) < 5]  # Assume max 5 passives
            if not eligible_units:
                break
                
            unit = random.choice(eligible_units)
            skill_cost = self.get_passive_cost(unit)
            
            if remaining_upgrade_budget >= skill_cost:
                # Get available passive skills for this unit
                if hasattr(unit, 'get_available_passive_skills'):
                    available_passives = unit.get_available_passive_skills()
                    if not available_passives:
                        continue  # No skills available for this unit type
                    
                    # Filter out skills the unit already has
                    eligible_passives = []
                    for passive_skill in available_passives:
                        # Check if unit already has this skill
                        skill_name = passive_skill.value if hasattr(passive_skill, 'value') else str(passive_skill)
                        has_skill = any(existing.name.lower().replace(" ", "_") == skill_name.lower().replace(" ", "_")
                                      for existing in unit.passive_skills)
                        if not has_skill:
                            eligible_passives.append(passive_skill)
                    
                    if eligible_passives:
                        skill_to_buy = random.choice(eligible_passives)
                        from skill_factory import create_skill
                        skill = create_skill(skill_to_buy)
                        if skill and unit.add_passive_skill(skill):
                            remaining_upgrade_budget -= skill_cost
                            if game:
                                game.add_message(f"Enemy bought {skill.name} for {unit.name} for {skill_cost} gold")
                        else:
                            # Failed to create/add skill, try another unit
                            continue
                    else:
                        # No eligible skills for this unit, try another
                        continue
                else:
                    # Unit doesn't have get_available_passive_skills method, skip
                    continue
            else:
                break  # Can't afford more upgrades
        
        # Phase 3: Buy augments with augment budget
        remaining_augment_budget = augment_budget + remaining_upgrade_budget
        enemy_augments = generate_augment_shop(20)  # Larger pool for enemy to choose from
        random.shuffle(enemy_augments)  # Randomize order
        
        for augment in enemy_augments:
            if remaining_augment_budget >= augment.cost:
                # 70% chance to buy each affordable augment (makes enemy slightly less optimal than player)
                if random.random() < 0.7:
                    # Set the augment's team to this team
                    augment.team = self
                    
                    # Let augment handle its own purchase logic
                    if augment.on_buy(self):
                        remaining_augment_budget -= augment.cost
                        self.add_augment(augment)
        
        # Equip items to enemy units randomly
        for item in self.unequipped_items[:]:  # Use slice copy to avoid modification during iteration
            available_units = [unit for unit in self.units if len(unit.items) < 3]
            if available_units:
                unit = random.choice(available_units)
                unit.add_item(item)
                self.unequipped_items.remove(item)
        
        total_spent = (unit_budget - remaining_unit_budget) + (upgrade_budget - remaining_upgrade_budget) + (augment_budget - remaining_augment_budget)
        if game:
            game.add_message(f"Enemy spent {total_spent} gold total, {budget - total_spent} left over")