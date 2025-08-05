from enum import Enum
from constants import FRAME_TIME

class VisualEffectType(Enum):
    """Types of visual effects that can be created."""
    FIRE = "fire"
    DARK = "dark"
    LIGHTNING = "lightning"
    ICE = "ice"
    HOLY = "holy"
    POISON = "poison"
    BLOOD = "blood"
    ARCANE = "arcane"

class VisualEffect:
    """A visual effect that appears on the board but has no gameplay impact."""
    
    # Global decay time for all visual effects (in seconds)
    DECAY_TIME = 1.0
    
    def __init__(self, effect_type: VisualEffectType, x: int, y: int):
        self.effect_type = effect_type
        self.x = x
        self.y = y
        self.remaining_time = self.DECAY_TIME
        self.max_time = self.DECAY_TIME
    
    def update(self, dt: float):
        """Update the visual effect, reducing its remaining time."""
        self.remaining_time -= dt
    
    def is_expired(self) -> bool:
        """Check if the visual effect has expired."""
        return self.remaining_time <= 0
    
    def get_alpha(self) -> float:
        """Get the alpha value (0.0 to 1.0) based on remaining time."""
        if self.remaining_time <= 0:
            return 0.0
        return self.remaining_time / self.max_time
    
    def get_position(self) -> tuple:
        """Get the position as a tuple."""
        return (self.x, self.y)