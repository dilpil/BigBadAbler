from typing import Optional, List

class Skill:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.owner = None
        self.skill_enum = None  # For passive skills, set to PassiveSkill enum
        
        self.is_passive = False
        self.cast_time = 1.0
        self.mana_cost = 100  # Amount of mana needed to cast
        self.current_mana = 0  # Current mana stored in the spell
        
        self.range = 5
        
    def update(self, dt: float):
        pass
    
    def add_mana(self, amount: float):
        """Add mana to the spell, capped at mana_cost"""
        if self.current_mana < self.mana_cost:
            self.current_mana = min(self.current_mana + amount, self.mana_cost)
    
    def is_on_cooldown(self) -> bool:
        return False  # No cooldowns anymore
    
    def start_cooldown(self):
        pass  # No cooldowns anymore
    
    def should_cast(self, caster) -> bool:
        return False
    
    def execute(self, caster):
        pass
    
    def on_event(self, event_type: str, **kwargs):
        pass
    
    # Helper methods for targeting
    def get_valid_targets(self, caster, target_team: str = "enemy", max_range: int = None) -> List:
        """Get valid targets within range based on team affiliation"""
        if max_range is None:
            max_range = self.range
            
        if target_team == "enemy":
            units = caster.board.enemy_units if caster.team == "player" else caster.board.player_units
        elif target_team == "ally":
            units = caster.board.player_units if caster.team == "player" else caster.board.enemy_units
        else:
            units = caster.board.get_all_units()
            
        valid_targets = []
        for unit in units:
            if not unit.is_alive():
                continue
            if caster.board.get_distance(caster, unit) <= max_range:
                valid_targets.append(unit)
                
        return valid_targets
    
    def get_targets_in_area(self, caster, center_x: int, center_y: int, radius: int, target_team: str = "enemy") -> List:
        """Get targets in an area of effect"""
        units = []
        for unit in caster.board.get_units_in_range(center_x, center_y, radius):
            if target_team == "enemy" and unit.team == caster.team:
                continue
            if target_team == "ally" and unit.team != caster.team:
                continue
            units.append(unit)
        return units
    
    def find_summon_position(self, caster) -> Optional[tuple]:
        """Find a valid position adjacent to the caster for summoning"""
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        for dx, dy in directions:
            x, y = caster.x + dx, caster.y + dy
            if caster.board.is_valid_position(x, y) and not caster.board.get_unit_at(x, y):
                return (x, y)
        return None
    
    def summon_minion(self, caster, minion, position):
        """Helper to summon a minion and fire the appropriate events"""
        x, y = position
        caster.board.add_unit(minion, x, y, caster.team)
        minion.board = caster.board
        minion.summoner = caster
        minion.is_summoned = True
        
        # Fire the OnMinionSummoned event
        caster.board.raise_event("minion_summoned", summoner=caster, minion=minion, skill=self)
        
        return minion
    
    def apply_to_owner(self, owner):
        """For passive skills - apply when owner is set"""
        self.owner = owner
        
    def remove_from_owner(self):
        """For passive skills - remove when owner is cleared"""
        self.owner = None
    
    def has_passive_skill(self, skill_name) -> bool:
        """Check if the owner has a specific passive skill"""
        if not self.owner:
            return False
        for passive in self.owner.passive_skills:
            # Handle both string and enum comparisons
            if hasattr(passive, 'skill_enum') and passive.skill_enum == skill_name:
                return True
            elif hasattr(skill_name, 'value') and passive.name.lower().replace(" ", "_") == skill_name.value:
                return True
            elif isinstance(skill_name, str) and passive.name.lower().replace(" ", "_") == skill_name.lower():
                return True
        return False