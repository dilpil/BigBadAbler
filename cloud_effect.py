"""
Cloud Effect system for persistent spell effects that remain on the board.
These effects can deal damage over time, heal, or apply other effects to units in their area.
"""

class CloudEffect:
    def __init__(self, name: str, x: float, y: float, radius: float, duration: float):
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.remaining_duration = duration
        self.source = None
        self.board = None
        self.tick_interval = 1.0  # Default to once per second
        self.tick_timer = 0.0
        
    def update(self, dt: float):
        """Update the cloud effect each frame"""
        self.remaining_duration -= dt
        self.tick_timer += dt
        
        if self.tick_timer >= self.tick_interval:
            self.tick_timer -= self.tick_interval
            self.on_tick()
    
    def is_expired(self) -> bool:
        """Check if this cloud effect has expired"""
        return self.remaining_duration <= 0
        
    def on_tick(self):
        """Called every tick_interval seconds - override in subclasses"""
        pass
        
    def get_units_in_radius(self, team_filter=None):
        """Get all units within the cloud's radius"""
        if not self.board:
            return []
            
        units = []
        for unit in self.board.get_all_units():
            distance = self.board.get_distance_to_point(unit, self.x, self.y)
            if distance <= self.radius:
                if team_filter is None or unit.team == team_filter:
                    units.append(unit)
        return units


class FirestormCloud(CloudEffect):
    """Firestorm cloud that deals fire damage over time"""
    def __init__(self, x: float, y: float, radius: float, damage_per_tick: float, source):
        super().__init__("Firestorm", x, y, radius, 2.0)  # 2 second duration
        self.damage_per_tick = damage_per_tick
        self.source = source
        self.tick_interval = 1.0  # Deal damage every second
        
    def on_tick(self):
        """Deal fire damage to all enemies in the area"""
        if not self.board:
            return
            
        # Get enemy units in radius
        enemies = []
        for unit in self.board.get_all_units():
            if unit.team != self.source.team and unit.is_alive():
                distance = self.board.get_distance_to_point(unit, self.x, self.y)
                if distance <= self.radius:
                    enemies.append(unit)
        
        # Deal damage to all enemies
        for enemy in enemies:
            enemy.take_damage(self.damage_per_tick, "fire", self.source)