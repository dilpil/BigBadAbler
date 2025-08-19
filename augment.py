from abc import ABC, abstractmethod

class Augment(ABC):
    """Base class for all augments that can be purchased from the shop"""
    
    def __init__(self, name, description, cost):
        self.name = name
        self.description = description
        self.cost = cost
        self.game = None  # Will be set when purchased
        
    @abstractmethod
    def on_buy(self, game):
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
        
    def on_buy(self, game):
        """Add the unit to the player's available units"""
        self.game = game
        unit = self.unit_factory()
        # Find first empty slot on player's side
        for x in range(4):  # Player units on left half
            for y in range(8):
                if not game.board.get_unit_at(x, y):
                    game.board.add_unit(unit, x, y, "player")
                    game.player_units.append(unit)
                    return True
        return False  # No space available


class ItemAugment(Augment):
    """Augment that provides an item when purchased"""
    
    def __init__(self, name, description, cost, item_factory):
        super().__init__(name, description, cost)
        self.item_factory = item_factory
        
    def on_buy(self, game):
        """Add the item to the player's inventory"""
        self.game = game
        item = self.item_factory()
        # Add to player's unequipped items
        if not hasattr(game, 'unequipped_items'):
            game.unequipped_items = []
        game.unequipped_items.append(item)
        return True


class PassiveAugment(Augment):
    """Augment that provides a passive bonus"""
    
    def __init__(self, name, description, cost):
        super().__init__(name, description, cost)
        self.active = False
        
    def on_buy(self, game):
        """Activate the passive effect"""
        self.game = game
        self.active = True
        # Add to game's passive augments list
        if not hasattr(game, 'passive_augments'):
            game.passive_augments = []
        game.passive_augments.append(self)
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