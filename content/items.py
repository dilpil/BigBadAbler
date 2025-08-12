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
        super().__init__("Sword", "+15 Attack Damage", 30)
        self.stats = {"attack_damage": 15}


class Staff(Item):
    def __init__(self):
        super().__init__("Staff", "+15 Ability Power", 30)
        self.stats = {"intelligence": 15}


class Armor(Item):
    def __init__(self):
        super().__init__("Armor", "+20 Armor", 30)
        self.stats = {"armor": 20}


class Cloak(Item):
    def __init__(self):
        super().__init__("Cloak", "+20 Magic Resist", 30)
        self.stats = {"magic_resist": 20}


class Boots(Item):
    def __init__(self):
        super().__init__("Boots", "+15% Attack Speed", 25)
        self.stats = {"attack_speed": 15}


class Ring(Item):
    def __init__(self):
        super().__init__("Ring", "+20 Max Mana", 35)
        self.stats = {"max_mp": 20}


class Amulet(Item):
    def __init__(self):
        super().__init__("Amulet", "+150 Max HP", 35)
        self.stats = {"max_hp": 150}


class Axe(Item):
    def __init__(self):
        super().__init__("Axe", "+10 Attack Damage, +10% Crit", 30)
        self.stats = {"attack_damage": 10, "crit_chance": 10}


class Orb(Item):
    def __init__(self):
        super().__init__("Orb", "+15 Ability Power, +15 Mana", 40)
        self.stats = {"intelligence": 15, "max_mp": 15}


class Shield(Item):
    def __init__(self):
        super().__init__("Shield", "+15 Armor, +15 MR", 45)
        self.stats = {"armor": 15, "magic_resist": 15}


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