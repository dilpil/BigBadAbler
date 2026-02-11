import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import individual unit classes
from content.units.necromancer import create_necromancer, Necromancer
from content.units.paladin import create_paladin, Paladin
from content.units.pyromancer import create_pyromancer, Pyromancer
from content.units.berserker import create_berserker, Berserker
from content.units.cleric import create_cleric, Cleric
from content.units.assassin import create_assassin, Assassin
from content.units.magic_knight import create_magic_knight, MagicKnight
from content.units.wizard import create_wizard, Wizard
from content.units.ogre_shaman import create_ogre_shaman, OgreShaman
from content.units.yeti import create_yeti, Yeti
from content.units.slime import create_slime, Slime

from unit import Unit, UnitType

def create_unit(unit_type: UnitType) -> Unit:
    """Create a unit of the specified type"""
    unit_factories = {
        UnitType.NECROMANCER: create_necromancer,
        UnitType.PALADIN: create_paladin,
        UnitType.PYROMANCER: create_pyromancer,
        UnitType.BERSERKER: create_berserker,
        UnitType.CLERIC: create_cleric,
        UnitType.ASSASSIN: create_assassin,
        UnitType.MAGIC_KNIGHT: create_magic_knight,
        UnitType.WIZARD: create_wizard,
        UnitType.OGRE_SHAMAN: create_ogre_shaman,
        UnitType.YETI: create_yeti,
        UnitType.SLIME: create_slime
    }

    factory = unit_factories.get(unit_type)
    if factory:
        return factory()
    return None

def get_available_units():
    """Get list of all available unit types"""
    return [
        UnitType.NECROMANCER, UnitType.PALADIN, UnitType.PYROMANCER,
        UnitType.BERSERKER, UnitType.CLERIC, UnitType.ASSASSIN,
        UnitType.MAGIC_KNIGHT, UnitType.WIZARD, UnitType.OGRE_SHAMAN,
        UnitType.YETI, UnitType.SLIME
    ]

def get_unit_cost(unit_type: UnitType) -> int:
    """Get the cost of a specific unit type"""
    unit_classes = {
        UnitType.NECROMANCER: Necromancer,
        UnitType.PALADIN: Paladin,
        UnitType.PYROMANCER: Pyromancer,
        UnitType.BERSERKER: Berserker,
        UnitType.CLERIC: Cleric,
        UnitType.ASSASSIN: Assassin,
        UnitType.MAGIC_KNIGHT: MagicKnight,
        UnitType.WIZARD: Wizard,
        UnitType.OGRE_SHAMAN: OgreShaman,
        UnitType.YETI: Yeti,
        UnitType.SLIME: Slime
    }

    unit_class = unit_classes.get(unit_type)
    if unit_class:
        return unit_class.get_cost()
    return 50  # Default cost