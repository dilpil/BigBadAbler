import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import individual unit classes
from content.units.necromancer import create_necromancer, Necromancer
from content.units.paladin import create_paladin, Paladin
from content.units.pyromancer import create_pyromancer, Pyromancer
from content.units.berserker import create_berserker, Berserker

from unit import Unit, UnitType

def create_unit(unit_type: UnitType) -> Unit:
    """Create a unit of the specified type"""
    unit_factories = {
        UnitType.NECROMANCER: create_necromancer,
        UnitType.PALADIN: create_paladin,
        UnitType.PYROMANCER: create_pyromancer,
        UnitType.BERSERKER: create_berserker
    }
    
    factory = unit_factories.get(unit_type)
    if factory:
        return factory()
    return None

def get_available_units():
    """Get list of all available unit types"""
    return [UnitType.NECROMANCER, UnitType.PALADIN, UnitType.PYROMANCER, UnitType.BERSERKER]

def get_unit_cost(unit_type: UnitType) -> int:
    """Get the cost of a specific unit type"""
    unit_classes = {
        UnitType.NECROMANCER: Necromancer,
        UnitType.PALADIN: Paladin,
        UnitType.PYROMANCER: Pyromancer,
        UnitType.BERSERKER: Berserker
    }
    
    unit_class = unit_classes.get(unit_type)
    if unit_class:
        return unit_class.get_cost()
    return 50  # Default cost