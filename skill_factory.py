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
    
    return None

def get_skill_cost(skill_name: str) -> int:
    """Get the cost of a skill (legacy function for compatibility)"""
    return 25