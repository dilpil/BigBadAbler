import pygame
import random

class TextFloater:
    def __init__(self, x: int, y: int, text: str, color: tuple):
        self.grid_x = x  # Store grid coordinates
        self.grid_y = y
        self.text = str(text)
        self.color = color
        self.lifetime = 2.0  # Total lifetime: 2 seconds
        self.max_lifetime = 2.0
        self.fade_start_time = 0.5  # Start fading after 0.5 seconds
        
        # Movement properties - start fast, slow down over time
        self.initial_vy = -80.0  # Start moving up quickly (pixels per second)
        self.final_vy = -5.0  # End moving up slowly
        self.vertical_offset = 0.0  # Track total vertical movement in pixels
        
        # Add small random horizontal offset to prevent overlap (in pixels)
        self.horizontal_offset = random.uniform(-10, 10)
        
    def update(self, dt: float):
        """Update the text floater position and lifetime."""
        # Calculate current velocity based on lifetime (starts fast, slows down)
        progress = 1.0 - (self.lifetime / self.max_lifetime)  # 0 at start, 1 at end
        current_vy = self.initial_vy + (self.final_vy - self.initial_vy) * progress
        
        self.vertical_offset += current_vy * dt
        self.lifetime -= dt
        
    def is_alive(self) -> bool:
        """Check if the text floater should still be displayed."""
        return self.lifetime > 0
        
    def get_alpha(self) -> int:
        """Calculate the alpha value based on lifetime for fading effect."""
        if self.lifetime > self.fade_start_time:
            # No fading for first 2 seconds
            return 255
        else:
            # Fade out over the last 2 seconds
            fade_progress = self.lifetime / self.fade_start_time
            return int(255 * fade_progress)
            
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, board_x: int, board_y: int, tile_size: int):
        """Draw the text floater on the screen."""
        if not self.is_alive():
            return
            
        # Convert grid coordinates to screen coordinates
        # Center horizontally on the tile
        screen_x = board_x + self.grid_x * tile_size + tile_size // 2 + self.horizontal_offset
        # Position above the unit (start at top of tile and move up)
        screen_y = board_y + self.grid_y * tile_size - 10 + self.vertical_offset
        
        # Render text with alpha
        alpha = self.get_alpha()
        if alpha > 0:
            text_surface = font.render(self.text, True, self.color)
            text_surface.set_alpha(alpha)
            
            # Center the text horizontally and vertically
            text_rect = text_surface.get_rect()
            text_rect.center = (int(screen_x), int(screen_y))
            
            screen.blit(text_surface, text_rect)


class TextFloaterManager:
    def __init__(self):
        self.text_floaters = []
        
    def add_text_floater(self, x: int, y: int, text: str, color: tuple):
        """Add a new text floater at the specified grid position."""
        floater = TextFloater(x, y, text, color)
        self.text_floaters.append(floater)
        
    def update(self, dt: float):
        """Update all text floaters and remove expired ones."""
        self.text_floaters = [f for f in self.text_floaters if f.is_alive()]
        for floater in self.text_floaters:
            floater.update(dt)
            
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, board_x: int, board_y: int, tile_size: int):
        """Draw all active text floaters."""
        for floater in self.text_floaters:
            floater.draw(screen, font, board_x, board_y, tile_size)
            
    def clear(self):
        """Clear all text floaters."""
        self.text_floaters.clear()