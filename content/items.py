import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Item:
    def __init__(self, name: str, description: str, cost: int):
        self.name = name
        self.description = description
        self.cost = cost
        self.stats = {}
        
    def apply_to_unit(self, unit):
        for stat, value in self.stats.items():
            if hasattr(unit, stat):
                setattr(unit, stat, getattr(unit, stat) + value)
                
    def remove_from_unit(self, unit):
        for stat, value in self.stats.items():
            if hasattr(unit, stat):
                setattr(unit, stat, getattr(unit, stat) - value)
                
    def on_event(self, event_type: str, **kwargs):
        pass


class Sword(Item):
    def __init__(self):
        super().__init__("Sword", "+10 Attack Damage", 30)
        self.stats = {"attack_damage": 10}


class Staff(Item):
    def __init__(self):
        super().__init__("Staff", "+15 Intelligence", 30)
        self.stats = {"intelligence": 15}


class Armor(Item):
    def __init__(self):
        super().__init__("Armor", "+15 Armor", 30)
        self.stats = {"armor": 15}


class Cloak(Item):
    def __init__(self):
        super().__init__("Cloak", "+15 Magic Resist", 30)
        self.stats = {"magic_resist": 15}


class Boots(Item):
    def __init__(self):
        super().__init__("Boots", "+20% Attack Speed", 25)
        self.stats = {"attack_speed": 20}


class Ring(Item):
    def __init__(self):
        super().__init__("Ring", "+20 Max Mana, +2 MP Regen", 35)
        self.stats = {"max_mp": 20, "mp_regen": 2}


class Amulet(Item):
    def __init__(self):
        super().__init__("Amulet", "+30 Max HP, +2 HP Regen", 35)
        self.stats = {"max_hp": 30, "hp_regen": 2}


class Axe(Item):
    def __init__(self):
        super().__init__("Axe", "+15 Strength", 30)
        self.stats = {"strength": 15}


class Orb(Item):
    def __init__(self):
        super().__init__("Orb", "+10 Int, +10 MP", 40)
        self.stats = {"intelligence": 10, "max_mp": 10}


class Shield(Item):
    def __init__(self):
        super().__init__("Shield", "+10 Armor, +10 MR", 45)
        self.stats = {"armor": 10, "magic_resist": 10}


def create_item(item_name: str) -> Item:
    item_classes = {
        "sword": Sword,
        "staff": Staff,
        "armor": Armor,
        "cloak": Cloak,
        "boots": Boots,
        "ring": Ring,
        "amulet": Amulet,
        "axe": Axe,
        "orb": Orb,
        "shield": Shield
    }
    
    item_class = item_classes.get(item_name.lower())
    if item_class:
        return item_class()
    return None


def get_all_items():
    return ["sword", "staff", "armor", "cloak", "boots", "ring", "amulet", "axe", "orb", "shield"]


def generate_item_shop(count: int = 10) -> list:
    import random
    all_items = get_all_items()
    selected_items = random.sample(all_items, min(count, len(all_items)))
    return [create_item(item_name) for item_name in selected_items]