from content.units.sun_spirit import create_sun_spirit, SunSpirit
from content.units.crazed_thornhound import create_crazed_thornhound, CrazedThornhound
from content.units.pillar_of_bones import create_pillar_of_bones, PillarOfBones
from content.units.water_nymph import create_water_nymph, WaterNymph
from content.units.big_lips import create_big_lips, BigLips
from content.units.oakenheart import create_oakenheart, Oakenheart
from content.units.imp_torturer import create_imp_torturer, ImpTorturer
from content.units.mass_of_tentacles import create_mass_of_tentacles, MassOfTentacles
from content.units.flame_maiden import create_flame_maiden, FlameMaiden
from content.units.red_wyrm import create_red_wyrm, RedWyrm
from content.units.void_knight import create_void_knight, VoidKnight
from content.units.blood_ogre import create_blood_ogre, BloodOgre

from unit import Unit, UnitType

def create_unit(unit_type: UnitType) -> Unit:
    """Create a unit of the specified type"""
    unit_factories = {
        UnitType.SUN_SPIRIT: create_sun_spirit,
        UnitType.CRAZED_THORNHOUND: create_crazed_thornhound,
        UnitType.PILLAR_OF_BONES: create_pillar_of_bones,
        UnitType.WATER_NYMPH: create_water_nymph,
        UnitType.BIG_LIPS: create_big_lips,
        UnitType.OAKENHEART: create_oakenheart,
        UnitType.IMP_TORTURER: create_imp_torturer,
        UnitType.MASS_OF_TENTACLES: create_mass_of_tentacles,
        UnitType.FLAME_MAIDEN: create_flame_maiden,
        UnitType.RED_WYRM: create_red_wyrm,
        UnitType.VOID_KNIGHT: create_void_knight,
        UnitType.BLOOD_OGRE: create_blood_ogre,
    }

    factory = unit_factories.get(unit_type)
    if factory:
        return factory()
    return None

def get_available_units():
    """Get list of all available unit types"""
    return [
        UnitType.SUN_SPIRIT, UnitType.CRAZED_THORNHOUND, UnitType.PILLAR_OF_BONES,
        UnitType.WATER_NYMPH, UnitType.BIG_LIPS, UnitType.OAKENHEART,
        UnitType.IMP_TORTURER, UnitType.MASS_OF_TENTACLES, UnitType.FLAME_MAIDEN,
        UnitType.RED_WYRM, UnitType.VOID_KNIGHT, UnitType.BLOOD_OGRE,
    ]

def get_unit_cost(unit_type: UnitType) -> int:
    """Get the cost of a specific unit type"""
    unit_classes = {
        UnitType.SUN_SPIRIT: SunSpirit,
        UnitType.CRAZED_THORNHOUND: CrazedThornhound,
        UnitType.PILLAR_OF_BONES: PillarOfBones,
        UnitType.WATER_NYMPH: WaterNymph,
        UnitType.BIG_LIPS: BigLips,
        UnitType.OAKENHEART: Oakenheart,
        UnitType.IMP_TORTURER: ImpTorturer,
        UnitType.MASS_OF_TENTACLES: MassOfTentacles,
        UnitType.FLAME_MAIDEN: FlameMaiden,
        UnitType.RED_WYRM: RedWyrm,
        UnitType.VOID_KNIGHT: VoidKnight,
        UnitType.BLOOD_OGRE: BloodOgre,
    }

    unit_class = unit_classes.get(unit_type)
    if unit_class:
        return unit_class.get_cost()
    return 50
