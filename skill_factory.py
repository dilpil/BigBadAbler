"""
Skill factory for creating skills from all units.
This replaces content/skills.py and provides a centralized way to create skills.
"""

from skill import Skill

def create_skill(skill_name) -> Skill:
    """Create any skill by name, routing to the appropriate unit-specific factory"""
    # Don't modify the skill_name - pass it as-is to the unit-specific factories
    # They will handle both string and enum types
    
    # Try necromancer skills first
    try:
        from content.units.necromancer import create_necromancer_skill
        skill = create_necromancer_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass
    
    # Try paladin skills
    try:
        from content.units.paladin import create_paladin_skill
        skill = create_paladin_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass
    
    # Try pyromancer skills
    try:
        from content.units.pyromancer import create_pyromancer_skill
        skill = create_pyromancer_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass
    
    # Try berserker skills
    try:
        from content.units.berserker import create_berserker_skill
        skill = create_berserker_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    # Try cleric skills
    try:
        from content.units.cleric import create_cleric_skill
        skill = create_cleric_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    # Try assassin skills
    try:
        from content.units.assassin import create_assassin_skill
        skill = create_assassin_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    # Try magic knight skills
    try:
        from content.units.magic_knight import create_magic_knight_skill
        skill = create_magic_knight_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    # Try wizard skills
    try:
        from content.units.wizard import create_wizard_skill
        skill = create_wizard_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    # Try ogre shaman skills
    try:
        from content.units.ogre_shaman import create_ogre_shaman_skill
        skill = create_ogre_shaman_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    # Try yeti skills
    try:
        from content.units.yeti import create_yeti_skill
        skill = create_yeti_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    # Try slime skills
    try:
        from content.units.slime import create_slime_skill
        skill = create_slime_skill(skill_name)
        if skill:
            return skill
    except ImportError:
        pass

    return None

def get_skill_cost(skill_name: str) -> int:
    """Get the cost of a skill (legacy function for compatibility)"""
    return 25