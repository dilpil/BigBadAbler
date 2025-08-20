from abc import ABC, abstractmethod

class Augment(ABC):
    """Base class for all augments that can be purchased from the shop"""
    
    def __init__(self, name, description, cost):
        self.name = name
        self.description = description
        self.cost = cost
        self.team = None  # Will be set when purchased
        
    @abstractmethod
    def on_buy(self, team):
        """Called when this augment is purchased"""
        pass
        
    def get_tooltip(self):
        """Returns tooltip text for this augment"""
        return f"{self.name}\nCost: {self.cost}\n{self.description}"


class UnitAugment(Augment):
    """Augment that provides a unit when purchased"""
    
    def __init__(self, name, description, cost, unit_factory):
        super().__init__(name, description, cost)
        self.unit_factory = unit_factory
        
    def on_buy(self, team):
        """Add the unit to the team's available units"""
        self.team = team
        unit = self.unit_factory()
        # Find empty position for this team
        position = team.find_empty_position()
        if position:
            x, y = position
            if team.add_unit(unit, x, y):
                return True
        return False  # No space available


class ItemAugment(Augment):
    """Augment that provides an item when purchased"""
    
    def __init__(self, name, description, cost, item_factory):
        super().__init__(name, description, cost)
        self.item_factory = item_factory
        
    def on_buy(self, team):
        """Add the item to the team's inventory"""
        self.team = team
        item = self.item_factory()
        self.item = item  # Store reference to the created item
        # Add to team's unequipped items
        team.unequipped_items.append(item)
        return True
    
    def is_equipped(self):
        """Check if this augment's item is currently equipped"""
        if not hasattr(self, 'item') or not self.team:
            return False
        # Check if item is in unequipped items (means it's not equipped)
        return self.item not in self.team.unequipped_items


class PassiveAugment(Augment):
    """Augment that provides a passive bonus"""
    
    def __init__(self, name, description, cost):
        super().__init__(name, description, cost)
        self.active = False
        
    def on_buy(self, team):
        """Activate the passive effect"""
        self.team = team
        self.active = True
        return True
        
    def on_event(self, event_type, **kwargs):
        """Handle events for passive augments"""
        if not self.active:
            return
        # Subclasses should override this to respond to events
        pass
        
    def on_battle_start(self):
        """Called at the start of each battle"""
        # Subclasses should override this
        pass
        
    def on_round_end(self):
        """Called at the end of each round"""
        # Subclasses should override this
        pass