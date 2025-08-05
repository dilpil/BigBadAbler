import pygame
import sys
import math
from enum import Enum
from game import Game, GamePhase, GameMode

class ShopType(Enum):
    NONE = "none"
    UNIT = "unit"
    UPGRADE = "upgrade"

from content.unit_registry import create_unit, get_available_units, get_unit_cost
from unit import UnitType
from content.skills import create_skill, get_skill_cost
from content.items import generate_item_shop
from visual_effects import EffectManager
from visual_effect import VisualEffectType
from constants import FPS

class PyUI:
    def __init__(self):
        pygame.init()
        self.width = 1400
        self.height = 900
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("BigBadAbler - Autobattler")
        
        self.clock = pygame.time.Clock()
        self.fps = FPS
        
        self.game = Game(GameMode.ASYNC)
        
        self.tile_size = 60
        self.board_x = 400  # Center horizontally: (1400 - 600) / 2
        self.board_y = 110  # Center vertically: (900 - 600) / 2
        
        self.selected_unit = None
        self.dragging_unit = None
        self.drag_offset = (0, 0)
        
        self.colors = {
            'background': (20, 0, 40),
            'board_bg': (40, 20, 60),
            'tile_player': (60, 30, 80),
            'tile_enemy': (80, 30, 60),
            'tile_hover': (100, 50, 120),
            'tile_border': (100, 50, 150),
            'player_border': (100, 200, 255),
            'enemy_border': (255, 100, 100),
            'hp_bar': (0, 255, 0),
            'hp_bar_bg': (50, 50, 50),
            'mp_bar': (0, 100, 255),
            'mp_bar_bg': (30, 30, 50),
            'cast_bar': (255, 255, 0),
            'cast_bar_bg': (100, 100, 0),
            'text': (255, 255, 255),
            'button': (80, 40, 100),
            'button_hover': (100, 60, 120),
            'button_disabled': (40, 30, 50),
            'necromancer': (80, 0, 120),
            'paladin': (255, 200, 0),
            'pyromancer': (255, 100, 0),
            'berserker': (200, 50, 50),
            'skeleton': (150, 150, 150),
            'panel_bg': (30, 10, 50),
            'panel_border': (100, 50, 150),
            # Item colors
            'sword': (200, 50, 50),      # Red
            'staff': (100, 50, 200),      # Purple
            'armor': (150, 150, 150),     # Silver
            'cloak': (50, 100, 150),      # Dark blue
            'boots': (150, 100, 50),      # Brown
            'ring': (255, 215, 0),        # Gold
            'amulet': (50, 200, 200),     # Cyan
            'axe': (255, 100, 0),         # Orange
            'orb': (200, 100, 255),       # Light purple
            'shield': (100, 150, 100),    # Green
            
            # Visual effect colors
            'effect_fire': (255, 100, 0),        # Red-orange
            'effect_dark': (120, 0, 120),        # Dark purple
            'effect_lightning': (255, 255, 100), # Bright yellow
            'effect_ice': (100, 200, 255),       # Light blue
            'effect_holy': (255, 255, 200),      # Bright white-yellow
            'effect_poison': (100, 200, 100),    # Green
            'effect_blood': (200, 50, 50),       # Dark red
            'effect_arcane': (200, 100, 255)     # Purple
        }
        
        self.fonts = {
            'tiny': pygame.font.Font(None, 16),
            'small': pygame.font.Font(None, 20),
            'medium': pygame.font.Font(None, 30),
            'large': pygame.font.Font(None, 40),
            'huge': pygame.font.Font(None, 60)
        }
        
        self.shop_open = ShopType.NONE
        self.tooltip = None
        self.shop_hover_unit = None
        self.shop_hover_ability = None
        self.selected_item = None
        self.selected_item_index = None
        self.hovered_tile = None  # (x, y) of tile being hovered over
        self.effect_manager = EffectManager()
        
        # UI-only smooth movement tracking
        self.unit_visual_positions = {}  # unit_id -> (visual_x, visual_y, target_x, target_y, progress, duration)
        self.movement_duration = 0.3
        
        # Initialize the game after all attributes are set
        self.init_game()
        
    def init_game(self):
        self.game.available_units = get_available_units()
        self.game.available_items = generate_item_shop()
        self.game.start_new_round()
        # Clear visual positions when starting a new round
        self.unit_visual_positions.clear()
        
        # Game methods are now properly implemented in game.py
        
    def run(self):
        running = True
        dt = 0
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
                    
            self.update(dt)
            self.draw()
            
            dt = self.clock.tick(self.fps) / 1000.0
            
        pygame.quit()
        sys.exit()
        
    def get_item_letter(self, item_name):
        """Get the display letter for an item"""
        # Use first letter, but handle special cases
        letter_map = {
            'sword': 'S',
            'staff': 'T',
            'armor': 'A',
            'cloak': 'C',
            'boots': 'B',
            'ring': 'R',
            'amulet': 'M',  # aMulet to avoid conflict with Armor
            'axe': 'X',
            'orb': 'O',
            'shield': 'H'   # sHield to avoid conflict with Sword/Staff
        }
        return letter_map.get(item_name.lower(), item_name[0].upper())
        
    def get_item_color(self, item_name):
        """Get the color for an item"""
        return self.colors.get(item_name.lower(), (100, 100, 100))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_click(event.pos)
            elif event.button == 3:
                self.handle_right_click(event.pos)
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_unit:
                self.handle_drop(event.pos)
                
        elif event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event.pos)
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.game.phase == GamePhase.SHOPPING:
                    self.game.start_combat()
                    # Clear visual positions when starting combat
                    self.unit_visual_positions.clear()
                elif self.game.phase == GamePhase.COMBAT:
                    self.game.toggle_pause()
            elif event.key == pygame.K_PERIOD:
                if self.game.phase == GamePhase.SHOPPING:
                    self.game.start_combat_paused()
                    # Clear visual positions when starting combat
                    self.unit_visual_positions.clear()
                elif self.game.phase == GamePhase.COMBAT:
                    self.game.advance_one_frame()
            elif event.key == pygame.K_ESCAPE:
                # Cancel item selection or close shop
                if self.selected_item:
                    self.selected_item = None
                    self.selected_item_index = None
                else:
                    self.shop_open = ShopType.NONE
                
    def handle_click(self, pos):
        x, y = pos
        
        if self.shop_open != ShopType.NONE:
            if not self.is_click_in_shop(pos):
                self.shop_open = ShopType.NONE
            else:
                self.handle_shop_click(pos)
            return
            
        # Check item shop click
        if self.game.phase == GamePhase.SHOPPING and y > self.height - 150:
            self.handle_item_shop_click(pos)
            return
            
        grid_x, grid_y = self.screen_to_grid(x, y)
        if 0 <= grid_x < 10 and 0 <= grid_y < 10:
            unit = self.game.board.get_unit_at(grid_x, grid_y)
            if unit and unit.team == "player" and self.game.phase == GamePhase.SHOPPING:
                # If we have a selected item, try to buy it for this unit
                if self.selected_item:
                    if len(unit.items) < 3 and self.game.gold >= self.selected_item.cost:
                        if self.game.purchase_item(self.selected_item.name, unit):
                            # Clear selection after successful purchase
                            self.selected_item = None
                            self.selected_item_index = None
                else:
                    # Open passive skill shop on left click
                    self.selected_unit = unit
                    self.shop_open = ShopType.UPGRADE
            elif not unit and grid_x < 5 and self.game.phase == GamePhase.SHOPPING:
                if self.selected_item:
                    # Cancel item selection on empty tile click
                    self.selected_item = None
                    self.selected_item_index = None
                else:
                    # Open unit shop
                    self.shop_open = ShopType.UNIT
                    self.shop_position = (grid_x, grid_y)
                
    def handle_right_click(self, pos):
        # Cancel item selection on right click
        if self.selected_item:
            self.selected_item = None
            self.selected_item_index = None
            return
            
        grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
        if 0 <= grid_x < 10 and 0 <= grid_y < 10:
            unit = self.game.board.get_unit_at(grid_x, grid_y)
            if unit and unit.team == "player" and self.game.phase == GamePhase.SHOPPING:
                self.selected_unit = unit
                self.shop_open = ShopType.UPGRADE
                
    def handle_drop(self, pos):
        if not self.dragging_unit:
            return
            
        grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
        if 0 <= grid_x < 5 and 0 <= grid_y < 10:
            if not self.game.board.get_unit_at(grid_x, grid_y):
                # For player dragging, update position instantly (no animation)
                unit_id = self.dragging_unit.id
                if unit_id in self.unit_visual_positions:
                    del self.unit_visual_positions[unit_id]
                self.game.board.move_unit(self.dragging_unit, grid_x, grid_y)
                # Update original position for player units during shopping phase
                if self.game.phase == GamePhase.SHOPPING and self.dragging_unit.team == "player":
                    self.dragging_unit.original_x = grid_x
                    self.dragging_unit.original_y = grid_y
                
        self.dragging_unit = None
        
    def handle_mouse_motion(self, pos):
        # Reset shop hover state
        self.shop_hover_unit = None
        self.shop_hover_ability = None
        
        # Check if we're in a shop
        if self.shop_open == ShopType.UNIT:
            hover_unit = self.get_shop_hover_unit(pos)
            if hover_unit:
                self.shop_hover_unit = hover_unit
                # Create tooltip for hovered unit
                unit_instance = create_unit(hover_unit)
                self.tooltip = self.create_shop_unit_tooltip(unit_instance)
                return
            else:
                self.tooltip = None
                return
        elif self.shop_open == ShopType.UPGRADE:
            hover_ability = self.get_shop_hover_ability(pos)
            if hover_ability:
                self.shop_hover_ability = hover_ability
                # Create tooltip for hovered ability
                self.tooltip = self.create_ability_tooltip(hover_ability)
                return
            else:
                self.tooltip = None
                return
                
        grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
        if 0 <= grid_x < 10 and 0 <= grid_y < 10:
            # Track hovered tile for plus sign indicator
            self.hovered_tile = (grid_x, grid_y)
            
            unit = self.game.board.get_unit_at(grid_x, grid_y)
            if unit:
                self.tooltip = self.create_unit_tooltip(unit)
            else:
                self.tooltip = None
        else:
            # Clear hovered tile when mouse leaves board
            self.hovered_tile = None
            
            # Check item tooltip
            if self.game.phase == GamePhase.SHOPPING and pos[1] > self.height - 150:
                item_index = (pos[0] - 100) // 110
                if 0 <= item_index < len(self.game.item_shop):
                    item = self.game.item_shop[item_index]
                    self.tooltip = self.create_item_tooltip(item)
                else:
                    self.tooltip = None
            else:
                self.tooltip = None
                
    def handle_shop_click(self, pos):
        if self.shop_open == ShopType.UNIT:
            self._handle_unit_shop_click(pos)
        elif self.shop_open == ShopType.UPGRADE:
            self._handle_upgrade_shop_click(pos)
    
    def _handle_unit_shop_click(self, pos):
        units = get_available_units()
        shop_width = 480
        shop_height = 480
        shop_x = self.width // 2 - shop_width // 2
        shop_y = self.height // 2 - shop_height // 2
        cols = 4
        
        for i, unit_type in enumerate(units):
            x = shop_x + 40 + (i % cols) * 110
            y = shop_y + 80 + (i // cols) * 120
            
            if x <= pos[0] <= x + 100 and y <= pos[1] <= y + 100:
                cost = get_unit_cost(unit_type)
                if self.game.gold >= cost:
                    if self.game.purchase_unit(unit_type, self.shop_position[0], self.shop_position[1]):
                        pass  # Unit already has default skill set on creation
                self.shop_open = ShopType.NONE
                return
    
    def _handle_upgrade_shop_click(self, pos):
        if not self.selected_unit:
            return
            
        passive_skills = self.selected_unit.get_available_passive_skills()
        if not passive_skills:
            return
            
        shop_width = 500
        shop_height = 450
        shop_x = self.width // 2 - shop_width // 2
        shop_y = self.height // 2 - shop_height // 2
        cols = 2
        
        # Filter out skills the unit already has
        available_skills = []
        for skill_name in passive_skills:
            already_has = any(p.name.lower().replace(" ", "_") == skill_name.lower() 
                            for p in self.selected_unit.passive_skills)
            if not already_has:
                available_skills.append(skill_name)
        
        # Now check clicks on the filtered list
        row = 0
        col = 0
        for i, skill_name in enumerate(available_skills):
            x = shop_x + 20 + col * 230
            y = shop_y + 100 + row * 80
            
            if x <= pos[0] <= x + 220 and y <= pos[1] <= y + 70:
                cost = self.selected_unit.get_passive_skill_cost(skill_name)
                if self.game.gold >= cost:
                    success = self.game.purchase_passive_skill(self.selected_unit, skill_name)
                    if success:
                        self.shop_open = ShopType.NONE  # Only close shop on successful purchase
                # Do nothing if insufficient gold - shop stays open
                return
                
            col += 1
            if col >= cols:
                col = 0
                row += 1
                    
    def handle_item_shop_click(self, pos):
        if self.game.phase != GamePhase.SHOPPING:
            return
            
        item_index = (pos[0] - 100) // 110
        if 0 <= item_index < len(self.game.item_shop):
            item = self.game.item_shop[item_index]
            # Select item if we can afford it
            if self.game.gold >= item.cost:
                self.selected_item = item
                self.selected_item_index = item_index
            else:
                # Clear selection if clicking on unaffordable item
                self.selected_item = None
                self.selected_item_index = None
            
    def get_shop_hover_unit(self, pos):
        """Check if mouse is hovering over a unit in the unit shop"""
        if self.shop_open != ShopType.UNIT:
            return None
            
        units = get_available_units()
        shop_width = 480
        shop_height = 480
        shop_x = self.width // 2 - shop_width // 2
        shop_y = self.height // 2 - shop_height // 2
        cols = 4
        
        for i, unit_type in enumerate(units):
            x = shop_x + 40 + (i % cols) * 110
            y = shop_y + 80 + (i // cols) * 120
            
            if x <= pos[0] <= x + 100 and y <= pos[1] <= y + 100:
                return unit_type
        return None
    
    def get_shop_hover_ability(self, pos):
        """Check if mouse is hovering over an ability in the upgrade shop"""
        if self.shop_open != ShopType.UPGRADE or not self.selected_unit:
            return None
            
        passive_skills = self.selected_unit.get_available_passive_skills()
        if not passive_skills:
            return None
            
        # Filter out skills the unit already has
        available_skills = []
        for skill_name in passive_skills:
            already_has = any(p.name.lower().replace(" ", "_") == skill_name.lower() 
                            for p in self.selected_unit.passive_skills)
            if not already_has:
                available_skills.append(skill_name)
        
        if not available_skills:
            return None
            
        shop_width = 500
        shop_height = 450
        shop_x = self.width // 2 - shop_width // 2
        shop_y = self.height // 2 - shop_height // 2
        cols = 2
        
        for i, skill_name in enumerate(available_skills):
            row = i // cols
            col = i % cols
            x = shop_x + 20 + col * 230
            y = shop_y + 100 + row * 80
            
            if x <= pos[0] <= x + 220 and y <= pos[1] <= y + 70:
                return skill_name
        return None
    
    def is_click_in_shop(self, pos):
        if self.shop_open == ShopType.UNIT:
            shop_width = 480
            shop_height = 480
            shop_x = self.width // 2 - shop_width // 2
            shop_y = self.height // 2 - shop_height // 2
            return (shop_x <= pos[0] <= shop_x + shop_width and 
                   shop_y <= pos[1] <= shop_y + shop_height)
        elif self.shop_open == ShopType.UPGRADE:
            shop_width = 500
            shop_height = 450
            shop_x = self.width // 2 - shop_width // 2
            shop_y = self.height // 2 - shop_height // 2
            return (shop_x <= pos[0] <= shop_x + shop_width and 
                   shop_y <= pos[1] <= shop_y + shop_height)
        return False
        
    def screen_to_grid(self, x, y):
        grid_x = (x - self.board_x) // self.tile_size
        grid_y = (y - self.board_y) // self.tile_size
        return grid_x, grid_y
        
    def update(self, dt):
        # Track unit position changes for smooth movement
        if self.game.phase == GamePhase.COMBAT:
            for unit in self.game.board.get_all_units():
                unit_id = unit.id
                
                # Check if unit moved to start animation
                if unit_id not in self.unit_visual_positions:
                    # Initialize visual position
                    self.unit_visual_positions[unit_id] = {
                        'visual_x': float(unit.x),
                        'visual_y': float(unit.y),
                        'last_x': unit.x,
                        'last_y': unit.y,
                        'target_x': None,
                        'target_y': None,
                        'progress': 0,
                        'start_x': 0,
                        'start_y': 0
                    }
                else:
                    pos_data = self.unit_visual_positions[unit_id]
                    
                    # Check if unit changed position
                    if unit.x != pos_data['last_x'] or unit.y != pos_data['last_y']:
                        # Start smooth movement animation
                        pos_data['start_x'] = pos_data['visual_x']
                        pos_data['start_y'] = pos_data['visual_y']
                        pos_data['target_x'] = float(unit.x)
                        pos_data['target_y'] = float(unit.y)
                        pos_data['progress'] = 0
                        pos_data['last_x'] = unit.x
                        pos_data['last_y'] = unit.y
                        
                    # Update animation
                    if pos_data['target_x'] is not None:
                        pos_data['progress'] += dt / self.movement_duration
                        if pos_data['progress'] >= 1.0:
                            # Animation complete
                            pos_data['visual_x'] = pos_data['target_x']
                            pos_data['visual_y'] = pos_data['target_y']
                            pos_data['target_x'] = None
                            pos_data['target_y'] = None
                            pos_data['progress'] = 0
                        else:
                            # Interpolate with easing
                            t = pos_data['progress']
                            eased_t = t * t * (3.0 - 2.0 * t)  # Smoothstep
                            
                            pos_data['visual_x'] = pos_data['start_x'] + (pos_data['target_x'] - pos_data['start_x']) * eased_t
                            pos_data['visual_y'] = pos_data['start_y'] + (pos_data['target_y'] - pos_data['start_y']) * eased_t
                
                # Check for damage events
                if hasattr(unit, '_last_hp'):
                    if unit.hp < unit._last_hp:
                        damage = unit._last_hp - unit.hp
                        visual_x = self.unit_visual_positions[unit_id]['visual_x']
                        visual_y = self.unit_visual_positions[unit_id]['visual_y']
                        x = self.board_x + visual_x * self.tile_size + self.tile_size // 2
                        y = self.board_y + visual_y * self.tile_size + self.tile_size // 2
                        self.effect_manager.add_particle_burst(x, y, (255, 255, 255), count=5)
                unit._last_hp = unit.hp
                
            # Store the current phase before update
            prev_phase = self.game.phase
            self.game.update_combat(dt)
            # If phase changed from combat to shopping, clear visual positions
            if prev_phase == GamePhase.COMBAT and self.game.phase == GamePhase.SHOPPING:
                self.unit_visual_positions.clear()
        else:
            # In shopping phase, sync visual positions immediately
            for unit in self.game.board.get_all_units():
                unit_id = unit.id
                if unit_id not in self.unit_visual_positions:
                    self.unit_visual_positions[unit_id] = {
                        'visual_x': float(unit.x),
                        'visual_y': float(unit.y),
                        'last_x': unit.x,
                        'last_y': unit.y,
                        'target_x': None,
                        'target_y': None,
                        'progress': 0,
                        'start_x': 0,
                        'start_y': 0
                    }
                else:
                    pos_data = self.unit_visual_positions[unit_id]
                    pos_data['visual_x'] = float(unit.x)
                    pos_data['visual_y'] = float(unit.y)
                    pos_data['last_x'] = unit.x
                    pos_data['last_y'] = unit.y
                    pos_data['target_x'] = None
                    pos_data['target_y'] = None
            
        self.effect_manager.update(dt)
            
    def draw(self):
        self.screen.fill(self.colors['background'])
        
        self.draw_board()
        self.draw_tile_indicators()
        self.draw_visual_effects()
        self.draw_units()
        self.draw_projectiles()
        self.draw_text_floaters()
        self.draw_ui()
        self.effect_manager.draw(self.screen, self.fonts['small'])
        
        if self.shop_open != ShopType.NONE:
            self.draw_shop()
            
        if self.tooltip:
            self.draw_tooltip()
            
        if self.dragging_unit:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.draw_unit_at(self.dragging_unit, mouse_x - self.drag_offset[0], 
                            mouse_y - self.drag_offset[1], alpha=128)
            
        pygame.display.flip()
        
    def draw_board(self):
        board_width = 10 * self.tile_size
        board_height = 10 * self.tile_size
        
        # Draw board background with border
        pygame.draw.rect(self.screen, self.colors['panel_border'],
                        (self.board_x - 15, self.board_y - 15, 
                         board_width + 30, board_height + 30))
        pygame.draw.rect(self.screen, self.colors['board_bg'],
                        (self.board_x - 10, self.board_y - 10, 
                         board_width + 20, board_height + 20))
        
        # Draw grid lines
        for i in range(11):
            # Vertical lines
            x = self.board_x + i * self.tile_size
            pygame.draw.line(self.screen, self.colors['tile_border'],
                           (x, self.board_y), (x, self.board_y + board_height), 1)
            # Horizontal lines
            y = self.board_y + i * self.tile_size
            pygame.draw.line(self.screen, self.colors['tile_border'],
                           (self.board_x, y), (self.board_x + board_width, y), 1)
            
        # Draw middle divider
        mid_x = self.board_x + 5 * self.tile_size
        pygame.draw.line(self.screen, self.colors['player_border'],
                       (mid_x, self.board_y), (mid_x, self.board_y + board_height), 3)
        
        # Draw tiles with different colors for each side
        for x in range(10):
            for y in range(10):
                tile_x = self.board_x + x * self.tile_size
                tile_y = self.board_y + y * self.tile_size
                
                # Different colors for player and enemy sides
                if x < 5:
                    color = self.colors['tile_player']
                else:
                    color = self.colors['tile_enemy']
                    
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if (tile_x <= mouse_x <= tile_x + self.tile_size and 
                    tile_y <= mouse_y <= tile_y + self.tile_size):
                    color = self.colors['tile_hover']
                    
                pygame.draw.rect(self.screen, color,
                               (tile_x + 2, tile_y + 2, self.tile_size - 4, self.tile_size - 4))
                               
    
    def draw_tile_indicators(self):
        """Draw plus sign indicator on empty tiles during shopping phase."""
        if (self.game.phase != GamePhase.SHOPPING or 
            not self.hovered_tile or 
            self.shop_open != ShopType.NONE):  # Don't show when shop is open
            return
            
        grid_x, grid_y = self.hovered_tile
        
        # Only show plus sign on player side (left 5 columns) for empty tiles
        if grid_x < 5 and not self.game.board.get_unit_at(grid_x, grid_y):
            # Calculate screen position
            x = self.board_x + grid_x * self.tile_size
            y = self.board_y + grid_y * self.tile_size
            
            # Draw plus sign
            plus_color = self.colors['player_border']  # Light blue color
            plus_size = self.tile_size // 3
            center_x = x + self.tile_size // 2
            center_y = y + self.tile_size // 2
            thickness = 4
            
            # Draw horizontal line of plus
            pygame.draw.rect(self.screen, plus_color,
                           (center_x - plus_size//2, center_y - thickness//2, 
                            plus_size, thickness))
            
            # Draw vertical line of plus
            pygame.draw.rect(self.screen, plus_color,
                           (center_x - thickness//2, center_y - plus_size//2, 
                            thickness, plus_size))
                               
    def draw_units(self):
        for unit in self.game.board.get_all_units():
            if unit != self.dragging_unit:
                # Use UI-tracked visual position for smooth movement
                unit_id = unit.id
                if unit_id in self.unit_visual_positions:
                    visual_x = self.unit_visual_positions[unit_id]['visual_x']
                    visual_y = self.unit_visual_positions[unit_id]['visual_y']
                else:
                    visual_x = float(unit.x)
                    visual_y = float(unit.y)
                    
                x = self.board_x + visual_x * self.tile_size
                y = self.board_y + visual_y * self.tile_size
                self.draw_unit_at(unit, x, y)
                
    def draw_unit_at(self, unit, x, y, alpha=255):
        # Apply visual effects
        offset_x = 0
        offset_y = 0
        
        # Bump effect
        if unit.bump_timer > 0:
            offset_x = unit.bump_direction[0] * unit.bump_timer * 30
            offset_y = unit.bump_direction[1] * unit.bump_timer * 30
            
        # Cast jump effect
        if unit.cast_jump_timer > 0:
            jump_height = math.sin(unit.cast_jump_timer * math.pi / 0.3) * 10
            offset_y -= jump_height
            
        # Death flash effect
        if unit.death_timer > 0:
            flash_phase = int(unit.death_timer * 10) % 2
            if flash_phase == 0:
                alpha = 128
                
        # Draw unit square
        unit_color = self.colors.get(unit.unit_type.value, (100, 100, 100))
        
        # Apply flash effect
        if unit.flash_timer > 0 and unit.flash_color:
            if unit.state.value == "casting":  # Continuous oscillating glow during casting
                # Calculate oscillating intensity based on cast progress
                cast_progress = unit.cast_timer / unit.cast_time if unit.cast_time > 0 else 0
                # Create oscillating effect with increasing intensity toward completion
                oscillation = math.sin(unit.cast_timer * 8) * 0.5 + 0.5  # Oscillates between 0 and 1
                base_intensity = 0.3 + (cast_progress * 0.4)  # Base intensity grows from 0.3 to 0.7
                flash_intensity = base_intensity + (oscillation * 0.3)  # Add oscillation
                flash_intensity = min(1.0, flash_intensity)  # Cap at 1.0
            else:
                # Normal flash effect for other cases
                flash_intensity = unit.flash_timer / unit.flash_duration
                
            unit_color = tuple(
                int(unit_color[i] * (1 - flash_intensity) + unit.flash_color[i] * flash_intensity)
                for i in range(3)
            )
        
        s = pygame.Surface((self.tile_size - 4, self.tile_size - 4))
        s.fill(unit_color)
        s.set_alpha(alpha)
        self.screen.blit(s, (x + offset_x + 2, y + offset_y + 2))
        
        # Draw border
        border_color = self.colors['player_border'] if unit.team == "player" else self.colors['enemy_border']
        pygame.draw.rect(self.screen, border_color,
                        (x + offset_x + 2, y + offset_y + 2, self.tile_size - 4, self.tile_size - 4), 3)
        
        # Draw unit letter
        letter = unit.unit_type.value[0].upper()
        text = self.fonts['large'].render(letter, True, self.colors['text'])
        text_rect = text.get_rect(center=(x + offset_x + self.tile_size // 2, 
                                         y + offset_y + self.tile_size // 2 - 5))
        self.screen.blit(text, text_rect)
        
        # Draw item indicators in upper left
        if unit.items:
            for i, item in enumerate(unit.items[:3]):  # Max 3 items
                item_x = x + offset_x + 4 + i * 14
                item_y = y + offset_y + 4
                item_color = self.get_item_color(item.name)
                
                # Draw colored square
                pygame.draw.rect(self.screen, item_color, (item_x, item_y, 12, 12))
                pygame.draw.rect(self.screen, (255, 255, 255), (item_x, item_y, 12, 12), 1)
                
                # Draw item letter
                letter = self.get_item_letter(item.name)
                text = self.fonts['tiny'].render(letter, True, self.colors['text'])
                text_rect = text.get_rect(center=(item_x + 6, item_y + 6))
                self.screen.blit(text, text_rect)
        
        # Draw status effect indicators below items
        if unit.status_effects:
            for i, status in enumerate(unit.status_effects[:4]):  # Max 4 shown
                status_x = x + offset_x + 4 + i * 14
                status_y = y + offset_y + 20  # Below items
                status_color = (200, 100, 255) if "buff" in status.name.lower() else (255, 100, 100)
                pygame.draw.rect(self.screen, status_color, (status_x, status_y, 12, 12))
                
        # Draw cast bar (only when casting)
        if unit.state.value == "casting" and unit.cast_time > 0:
            cast_bar_y = y + offset_y + self.tile_size - 18
            pygame.draw.rect(self.screen, self.colors['cast_bar_bg'],
                            (x + offset_x + 4, cast_bar_y, self.tile_size - 8, 4))
            cast_progress = unit.cast_timer / unit.cast_time
            cast_width = int((self.tile_size - 8) * cast_progress)
            if cast_width > 0:
                pygame.draw.rect(self.screen, self.colors['cast_bar'],
                                (x + offset_x + 4, cast_bar_y, cast_width, 4))
        
        # Draw HP bar
        hp_bar_y = y + offset_y + self.tile_size - 12
        pygame.draw.rect(self.screen, self.colors['hp_bar_bg'],
                        (x + offset_x + 4, hp_bar_y, self.tile_size - 8, 4))
        hp_width = int((self.tile_size - 8) * (unit.hp / unit.max_hp))
        if hp_width > 0:
            pygame.draw.rect(self.screen, self.colors['hp_bar'],
                            (x + offset_x + 4, hp_bar_y, hp_width, 4))
                            
        # Draw MP bar (shows spell mana)
        mp_bar_y = y + offset_y + self.tile_size - 6
        pygame.draw.rect(self.screen, self.colors['mp_bar_bg'],
                        (x + offset_x + 4, mp_bar_y, self.tile_size - 8, 4))
        
        # Show spell mana if unit has a spell
        if unit.spell and not unit.spell.is_passive:
            mp_ratio = unit.spell.current_mana / unit.spell.mana_cost if unit.spell.mana_cost > 0 else 0
            mp_width = int((self.tile_size - 8) * mp_ratio)
            if mp_width > 0:
                pygame.draw.rect(self.screen, self.colors['mp_bar'],
                                (x + offset_x + 4, mp_bar_y, mp_width, 4))
                            
    def draw_projectiles(self):
        for projectile in self.game.board.projectiles:
            x = self.board_x + projectile.x * self.tile_size + self.tile_size // 2
            y = self.board_y + projectile.y * self.tile_size + self.tile_size // 2
            
            # Different colors for different projectile types
            if hasattr(projectile, 'damage_type'):
                if projectile.damage_type == "magical":
                    color = (255, 100, 255)
                else:
                    color = (255, 255, 100)
            else:
                color = (255, 255, 0)
                
            # Draw glow effect
            for i in range(3):
                glow_color = tuple(c // (i + 1) for c in color)
                pygame.draw.circle(self.screen, glow_color, (int(x), int(y)), 8 - i * 2)
                
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 5)
    
    def draw_visual_effects(self):
        """Draw visual effects as fading transparent squares."""
        for effect in self.game.board.visual_effects:
            # Get effect position on screen
            x = self.board_x + effect.x * self.tile_size
            y = self.board_y + effect.y * self.tile_size
            
            # Get color for this effect type
            color_key = f'effect_{effect.effect_type.value}'
            base_color = self.colors.get(color_key, (255, 255, 255))
            
            # Calculate alpha based on remaining time
            alpha = int(effect.get_alpha() * 255)
            alpha = max(0, min(255, alpha))
            
            if alpha > 0:
                # Create a surface with per-pixel alpha
                effect_surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                
                # Draw the effect as a filled rectangle with alpha
                color_with_alpha = (*base_color, alpha)
                pygame.draw.rect(effect_surface, color_with_alpha, 
                               (0, 0, self.tile_size, self.tile_size))
                
                # Optional: Add a subtle border
                border_alpha = min(alpha, 100)
                border_color = (*base_color, border_alpha)
                pygame.draw.rect(effect_surface, border_color, 
                               (0, 0, self.tile_size, self.tile_size), 2)
                
                # Blit the effect surface to the screen
                self.screen.blit(effect_surface, (x, y))
    
    def draw_text_floaters(self):
        """Draw text floaters from the board's text floater manager."""
        self.game.board.text_floater_manager.draw(
            self.screen, 
            self.fonts['small'], 
            self.board_x, 
            self.board_y, 
            self.tile_size
        )
            
    def draw_ui(self):
        # Top panel
        panel_height = 80
        pygame.draw.rect(self.screen, self.colors['panel_bg'], (0, 0, self.width, panel_height))
        pygame.draw.line(self.screen, self.colors['panel_border'], 
                        (0, panel_height), (self.width, panel_height), 3)
        
        # Game stats
        y = 25
        stats = [
            (f"Round: {self.game.round}", 50),
            (f"Lives: {self.game.player_lives}/5", 200),
            (f"Wins: {self.game.player_wins}/20", 350),
            (f"Gold: {self.game.gold}", 500),
        ]
        
        for text, x in stats:
            rendered = self.fonts['medium'].render(text, True, self.colors['text'])
            self.screen.blit(rendered, (x, y))
            
        # Phase indicator
        phase_text = "SHOPPING PHASE" if self.game.phase == GamePhase.SHOPPING else "COMBAT PHASE"
        phase_color = self.colors['player_border'] if self.game.phase == GamePhase.SHOPPING else self.colors['enemy_border']
        text = self.fonts['large'].render(phase_text, True, phase_color)
        self.screen.blit(text, (800, 20))
        
        # Battle frame counter and controls (only during combat)
        if self.game.phase == GamePhase.COMBAT:
            frame_text = f"Frame: {self.game.combat_frame}"
            if self.game.paused:
                frame_text += " (PAUSED)"
            text = self.fonts['medium'].render(frame_text, True, self.colors['text'])
            self.screen.blit(text, (800, 55))
            
        
        if self.game.phase == GamePhase.SHOPPING:
            
            # Show selected item info
            if self.selected_item:
                text = self.fonts['medium'].render(f"Selected: {self.selected_item.name}", True, (255, 200, 0))
                self.screen.blit(text, (250, self.height - 200))
                text = self.fonts['small'].render("Click a unit to equip", True, self.colors['text'])
                self.screen.blit(text, (250, self.height - 170))
            
            # Item shop panel
            shop_y = self.height - 160
            pygame.draw.rect(self.screen, self.colors['panel_bg'], 
                           (0, shop_y, self.width, 160))
            pygame.draw.line(self.screen, self.colors['panel_border'], 
                           (0, shop_y), (self.width, shop_y), 3)
            
            text = self.fonts['medium'].render("ITEM SHOP", True, self.colors['text'])
            self.screen.blit(text, (50, shop_y + 10))
            
            # Draw items
            for i, item in enumerate(self.game.item_shop):
                x = 100 + i * 110
                y = shop_y + 50
                
                # Item background with selection highlight
                can_afford = self.game.gold >= item.cost
                is_selected = self.selected_item_index == i
                
                if is_selected:
                    # Draw selection glow
                    for j in range(3):
                        glow_alpha = 150 - (j * 40)
                        glow_surface = pygame.Surface((106 + j * 4, 86 + j * 4))
                        glow_surface.fill((255, 200, 0))
                        glow_surface.set_alpha(glow_alpha)
                        self.screen.blit(glow_surface, (x - 3 - j * 2, y - 3 - j * 2))
                
                color = self.colors['button'] if can_afford else self.colors['button_disabled']
                pygame.draw.rect(self.screen, color, (x, y, 100, 80))
                border_color = (255, 200, 0) if is_selected else self.colors['panel_border']
                border_width = 3 if is_selected else 2
                pygame.draw.rect(self.screen, border_color, (x, y, 100, 80), border_width)
                
                # Draw item as colored square with letter
                item_color = self.get_item_color(item.name)
                item_size = 40
                item_x = x + (100 - item_size) // 2
                item_y = y + 10
                
                # Apply transparency if can't afford
                if not can_afford:
                    s = pygame.Surface((item_size, item_size))
                    s.fill(item_color)
                    s.set_alpha(100)
                    self.screen.blit(s, (item_x, item_y))
                else:
                    pygame.draw.rect(self.screen, item_color, (item_x, item_y, item_size, item_size))
                    
                # Draw item letter
                letter = self.get_item_letter(item.name)
                text_color = self.colors['text'] if can_afford else (100, 100, 100)
                text = self.fonts['medium'].render(letter, True, text_color)
                text_rect = text.get_rect(center=(item_x + item_size // 2, item_y + item_size // 2))
                self.screen.blit(text, text_rect)
                
                # Item name below the square
                text = self.fonts['tiny'].render(item.name, True, self.colors['text'])
                text_rect = text.get_rect(center=(x + 50, y + 58))
                self.screen.blit(text, text_rect)
                
                # Cost
                text = self.fonts['small'].render(f"{item.cost}g", True, 
                                                 self.colors['text'] if can_afford else (100, 100, 100))
                text_rect = text.get_rect(center=(x + 50, y + 70))
                self.screen.blit(text, text_rect)
                
        else:
            # Combat log - positioned below board, centered, 75% width
            log_height = 160
            log_width = int(self.width * 0.75)  # 75% of screen width
            log_x = (self.width - log_width) // 2  # Center horizontally
            log_y = 730  # Below the board (board ends at 710)
            
            pygame.draw.rect(self.screen, self.colors['panel_bg'], 
                           (log_x, log_y, log_width, log_height))
            pygame.draw.rect(self.screen, self.colors['panel_border'], 
                           (log_x, log_y, log_width, log_height), 3)
            
            text = self.fonts['medium'].render("COMBAT LOG", True, self.colors['text'])
            text_rect = text.get_rect(center=(self.width // 2, log_y + 20))
            self.screen.blit(text, text_rect)
            
            # Draw messages
            y = log_y + 40
            for message in self.game.message_log[-6:]:  # Reduced to 6 messages due to smaller height
                text = self.fonts['small'].render(message, True, self.colors['text'])
                self.screen.blit(text, (log_x + 20, y))
                y += 20
                
    def draw_shop(self):
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        if self.shop_open == ShopType.UNIT:
            self.draw_unit_shop()
        elif self.shop_open == ShopType.UPGRADE:
            self.draw_passive_skill_shop()
            
    def draw_unit_shop(self):
        units = get_available_units()
        shop_width = 480
        shop_height = 480
        shop_x = self.width // 2 - shop_width // 2
        shop_y = self.height // 2 - shop_height // 2
        
        # Shop background
        pygame.draw.rect(self.screen, self.colors['panel_bg'], 
                       (shop_x, shop_y, shop_width, shop_height))
        pygame.draw.rect(self.screen, self.colors['panel_border'], 
                       (shop_x, shop_y, shop_width, shop_height), 3)
        
        # Title
        title = self.fonts['large'].render("CHOOSE A UNIT", True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, shop_y + 30))
        self.screen.blit(title, title_rect)
        
        # Units
        cols = 4
        for i, unit_type in enumerate(units):
            x = shop_x + 40 + (i % cols) * 110
            y = shop_y + 80 + (i // cols) * 120
            
            cost = get_unit_cost(unit_type)
            can_afford = self.game.gold >= cost
            color = self.colors['button'] if can_afford else self.colors['button_disabled']
            
            # Add hover highlight
            if self.shop_hover_unit == unit_type:
                # Glowing hover effect
                hover_color = self.colors['button_hover']
                # Draw glow effect
                for i in range(3):
                    glow_alpha = 100 - (i * 30)
                    glow_surface = pygame.Surface((106 + i * 4, 106 + i * 4))
                    glow_surface.fill(hover_color)
                    glow_surface.set_alpha(glow_alpha)
                    self.screen.blit(glow_surface, (x - 3 - i * 2, y - 3 - i * 2))
                    
                color = hover_color
            
            # Unit card
            pygame.draw.rect(self.screen, color, (x, y, 100, 100))
            border_color = self.colors['player_border'] if self.shop_hover_unit == unit_type else self.colors['panel_border']
            border_width = 3 if self.shop_hover_unit == unit_type else 2
            pygame.draw.rect(self.screen, border_color, (x, y, 100, 100), border_width)
            
            # Unit preview
            unit_color = self.colors.get(unit_type.value, (100, 100, 100))
            pygame.draw.rect(self.screen, unit_color, (x + 25, y + 20, 50, 50))
            
            # Unit name
            text = self.fonts['small'].render(unit_type.value.capitalize(), True, self.colors['text'])
            text_rect = text.get_rect(center=(x + 50, y + 10))
            self.screen.blit(text, text_rect)
            
            # Cost
            text = self.fonts['medium'].render(f"{cost}g", True, 
                                             self.colors['text'] if can_afford else (100, 100, 100))
            text_rect = text.get_rect(center=(x + 50, y + 85))
            self.screen.blit(text, text_rect)
            
    def draw_passive_skill_shop(self):
        if not self.selected_unit:
            return
            
        passive_skills = self.selected_unit.get_available_passive_skills()
        if not passive_skills:
            # No passive skills available for this unit type
            shop_width = 400
            shop_height = 200
            shop_x = self.width // 2 - shop_width // 2
            shop_y = self.height // 2 - shop_height // 2
            
            # Shop background
            pygame.draw.rect(self.screen, self.colors['panel_bg'], 
                           (shop_x, shop_y, shop_width, shop_height))
            pygame.draw.rect(self.screen, self.colors['panel_border'], 
                           (shop_x, shop_y, shop_width, shop_height), 3)
            
            # Title
            title = self.fonts['large'].render(f"NO UPGRADES FOR {self.selected_unit.name.upper()}", 
                                             True, self.colors['text'])
            title_rect = title.get_rect(center=(self.width // 2, shop_y + 100))
            self.screen.blit(title, title_rect)
            return
            
        shop_width = 500
        shop_height = 450
        shop_x = self.width // 2 - shop_width // 2
        shop_y = self.height // 2 - shop_height // 2
        
        # Shop background with gradient
        pygame.draw.rect(self.screen, self.colors['panel_bg'], 
                       (shop_x, shop_y, shop_width, shop_height))
        pygame.draw.rect(self.screen, self.colors['panel_border'], 
                       (shop_x, shop_y, shop_width, shop_height), 3)
        
        # Header background
        header_rect = (shop_x, shop_y, shop_width, 80)
        pygame.draw.rect(self.screen, (50, 30, 70), header_rect)
        pygame.draw.rect(self.screen, self.colors['panel_border'], header_rect, 2)
        
        # Title
        title = self.fonts['large'].render(f"UPGRADES FOR {self.selected_unit.name.upper()}", 
                                         True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, shop_y + 30))
        self.screen.blit(title, title_rect)
        
        # Current passive skills count and gold
        text = self.fonts['small'].render(f"Current Upgrades: {len(self.selected_unit.passive_skills)}", 
                                        True, self.colors['text'])
        self.screen.blit(text, (shop_x + 20, shop_y + 60))
        
        gold_text = self.fonts['small'].render(f"Gold: {self.game.gold}g", 
                                             True, (255, 215, 0))  # Gold color
        self.screen.blit(gold_text, (shop_x + shop_width - 120, shop_y + 60))
        
        # Filter out skills the unit already has
        available_skills = []
        for skill_name in passive_skills:
            already_has = any(p.name.lower().replace(" ", "_") == skill_name.lower() 
                            for p in self.selected_unit.passive_skills)
            if not already_has:
                available_skills.append(skill_name)
        
        # Show message if no skills available
        if not available_skills:
            no_skills_text = self.fonts['medium'].render("All upgrades purchased!", True, self.colors['text'])
            no_skills_rect = no_skills_text.get_rect(center=(self.width // 2, shop_y + 200))
            self.screen.blit(no_skills_text, no_skills_rect)
            return
        
        # Passive skills grid
        cols = 2
        row = 0
        col = 0
        for skill_name in available_skills:
            x = shop_x + 20 + col * 230
            y = shop_y + 100 + row * 80
            
            cost = self.selected_unit.get_passive_skill_cost(skill_name)
            can_buy = self.game.gold >= cost
            is_hovered = self.shop_hover_ability == skill_name
            
            # Determine colors based on state
            if is_hovered and can_buy:
                color = self.colors['button_hover']
                border_color = (150, 100, 200)  # Purple highlight
                border_width = 3
            elif can_buy:
                color = self.colors['button']
                border_color = self.colors['panel_border']
                border_width = 2
            else:
                color = self.colors['button_disabled']
                border_color = (80, 80, 80)
                border_width = 2
            
            # Add glow effect for hovered abilities
            if is_hovered and can_buy:
                # Draw glow layers
                for i in range(3):
                    glow_alpha = 50 - (i * 15)
                    glow_surface = pygame.Surface((226 + i * 4, 76 + i * 4))
                    glow_surface.set_alpha(glow_alpha)
                    glow_surface.fill((150, 100, 200))
                    self.screen.blit(glow_surface, (x - 3 - i * 2, y - 3 - i * 2))
            
            # Skill card background
            pygame.draw.rect(self.screen, color, (x, y, 220, 70))
            pygame.draw.rect(self.screen, border_color, (x, y, 220, 70), border_width)
            
            # Add subtle gradient effect
            if can_buy:
                gradient_surface = pygame.Surface((220, 70))
                gradient_surface.set_alpha(30)
                gradient_color = (255, 255, 255) if is_hovered else (200, 200, 200)
                gradient_surface.fill(gradient_color)
                self.screen.blit(gradient_surface, (x, y))
            
            # Skill name (larger and more prominent)
            display_name = skill_name.replace("_", " ").title()
            text = self.fonts['medium'].render(display_name, True, self.colors['text'])
            self.screen.blit(text, (x + 10, y + 10))
            
            # Cost (styled with background)
            cost_text = f"{cost}g"
            cost_color = self.colors['text'] if can_buy else (120, 120, 120)
            # Cost background
            cost_bg_rect = (x + 160, y + 45, 50, 20)
            cost_bg_color = (40, 20, 60) if can_buy else (30, 30, 30)
            pygame.draw.rect(self.screen, cost_bg_color, cost_bg_rect)
            pygame.draw.rect(self.screen, border_color, cost_bg_rect, 1)
            
            text = self.fonts['small'].render(cost_text, True, cost_color)
            text_rect = text.get_rect(center=(x + 185, y + 55))
            self.screen.blit(text, text_rect)
            
            # Type indicator (show "PASSIVE" text)
            type_text = self.fonts['tiny'].render("PASSIVE", True, (150, 150, 200))
            self.screen.blit(type_text, (x + 10, y + 50))
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
            
    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long for a single line
                    lines.append(word)
                    
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines
    
    def draw_tooltip(self):
        if not self.tooltip:
            return
            
        raw_lines = self.tooltip.split('\\n')
        max_tooltip_width = 350  # Maximum width for tooltips
        
        # Process lines and handle text wrapping
        lines = []
        for raw_line in raw_lines:
            if raw_line.strip():
                # Wrap long lines
                wrapped = self.wrap_text(raw_line, self.fonts['small'], max_tooltip_width - 20)
                lines.extend(wrapped)
            else:
                lines.append('')  # Preserve empty lines
        
        # Calculate tooltip dimensions with proper padding
        max_width = 0
        line_heights = []
        
        for line in lines:
            if line.strip():  # Non-empty line
                text_width = self.fonts['small'].size(line)[0]
                max_width = max(max_width, text_width)
                line_heights.append(20)  # Slightly more spacing for readability
            else:  # Empty line
                line_heights.append(10)
        
        width = min(max_width + 30, max_tooltip_width)  # Use consistent max width
        height = sum(line_heights) + 20  # More padding for better appearance
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Position tooltip to avoid going off screen
        x = mouse_x + 15
        y = mouse_y + 15
        
        if x + width > self.width:
            x = mouse_x - width - 15
        if y + height > self.height:
            y = mouse_y - height - 15
            
        # Ensure tooltip stays on screen
        x = max(5, min(x, self.width - width - 5))
        y = max(5, min(y, self.height - height - 5))
        
        # Tooltip background with subtle border
        pygame.draw.rect(self.screen, (25, 15, 45), (x, y, width, height))
        pygame.draw.rect(self.screen, self.colors['panel_border'], (x, y, width, height), 2)
        
        # Tooltip text with better positioning
        current_y = y + 10
        for i, line in enumerate(lines):
            if line.strip():  # Non-empty line
                # Determine original line type for coloring
                # (Check against original lines to maintain color coding)
                is_header = False
                is_bullet = False
                is_stat = False
                is_description = False
                
                # Find which original line this wrapped line came from
                for raw_line in raw_lines:
                    if line in raw_line:
                        if raw_line.startswith('•'):
                            is_bullet = True
                        elif raw_line.startswith('  ['):
                            is_stat = True
                        elif raw_line.startswith('  ') and not raw_line.startswith('  ['):
                            is_description = True
                        elif raw_line.isupper() and ':' in raw_line:
                            is_header = True
                        break
                
                # Choose font color based on content type
                if is_bullet or line.startswith('•'):
                    color = (255, 255, 100)  # Yellow for bullet points
                elif is_stat:
                    color = (150, 150, 200)  # Light blue for stats
                elif is_description:
                    color = (200, 200, 200)  # Light gray for descriptions
                elif is_header:
                    color = (255, 150, 255)  # Pink for section headers
                else:
                    color = self.colors['text']  # White for main text
                    
                text = self.fonts['small'].render(line, True, color)
                self.screen.blit(text, (x + 15, current_y))
                
            current_y += line_heights[i]
            
    def create_unit_tooltip(self, unit):
        lines = [
            f"{unit.name} ({unit.unit_type.value.capitalize()})",
            f"HP: {int(unit.hp)}/{unit.max_hp} | MP Regen: {unit.mp_regen}/s",
            f"AD: {unit.attack_damage} | Range: {unit.attack_range} | AS: {unit.attack_speed}%",
            f"STR: {unit.strength} | INT: {unit.intelligence}",
            f"Armor: {unit.armor} | Magic Resist: {unit.magic_resist}",
            ""
        ]
        
        if unit.spell:
            lines.append("SPELL:")
            skill = unit.spell
            lines.append(f"• {skill.name}")
            
            # Add skill description if available
            if hasattr(skill, 'description') and skill.description:
                lines.append(f"  {skill.description}")
            
            # Add skill stats
            skill_stats = []
            
            if skill.is_passive:
                skill_stats.append("Passive")
            else:
                if hasattr(skill, 'cast_time') and skill.cast_time is not None:
                    skill_stats.append(f"Cast: {skill.cast_time}s")
                if hasattr(skill, 'mana_cost') and skill.mana_cost is not None and skill.mana_cost > 0:
                    skill_stats.append(f"Mana: {skill.mana_cost}")
                    
                # Show current mana
                if hasattr(skill, 'current_mana'):
                    lines.append(f"  Current Mana: {int(skill.current_mana)}/{skill.mana_cost}")
            
            if hasattr(skill, 'range') and skill.range is not None:
                skill_stats.append(f"Range: {skill.range}")
                
            if skill_stats:
                lines.append(f"  [{' | '.join(skill_stats)}]")
                
            # No more cooldowns to show
                
        if unit.passive_skills:
            lines.append("")
            lines.append("UPGRADES:")
            for passive in unit.passive_skills:
                lines.append(f"• {passive.name}")
                # Add passive skill description if available
                if hasattr(passive, 'description') and passive.description:
                    lines.append(f"  {passive.description}")
                
        if unit.items:
            lines.append("")
            lines.append("ITEMS:")
            for item in unit.items:
                lines.append(f"• {item.name}")
                if hasattr(item, 'description') and item.description:
                    lines.append(f"  {item.description}")
                    
        if unit.status_effects:
            lines.append("")
            lines.append("STATUS EFFECTS:")
            for status in unit.status_effects:
                duration_text = f" ({status.remaining_duration:.1f}s)" if hasattr(status, 'remaining_duration') else ""
                lines.append(f"• {status.name}{duration_text}")
                
        return '\\n'.join(lines)
    
    def create_shop_unit_tooltip(self, unit):
        """Create tooltip for units in the shop showing their base stats"""
        lines = [
            f"{unit.name} ({unit.unit_type.value.capitalize()})",
            f"Cost: {get_unit_cost(unit.unit_type)} gold",
            "",
            "BASE STATS:",
            f"HP: {unit.max_hp} | MP Regen: {unit.mp_regen}/s",
            f"Attack Damage: {unit.attack_damage}",
            f"Attack Range: {unit.attack_range}",
            f"Attack Speed: {unit.attack_speed}%",
            f"Strength: {unit.strength} | Intelligence: {unit.intelligence}",
            f"Armor: {unit.armor} | Magic Resist: {unit.magic_resist}",
            ""
        ]
        
        # Add current spell info (default skill is now set on creation)
        if unit.spell:
            lines.append("CURRENT SPELL:")
            lines.append(f"• {unit.spell.name}")
            if hasattr(unit.spell, 'description') and unit.spell.description:
                lines.append(f"  {unit.spell.description}")
                
            # Add skill stats
            skill_stats = []
            if unit.spell.is_passive:
                skill_stats.append("Passive")
            else:
                if hasattr(unit.spell, 'cast_time') and unit.spell.cast_time is not None:
                    skill_stats.append(f"Cast: {unit.spell.cast_time}s")
                if hasattr(unit.spell, 'cooldown_time') and unit.spell.cooldown_time is not None:
                    skill_stats.append(f"CD: {unit.spell.cooldown_time}s")
                if hasattr(unit.spell, 'mana_cost') and unit.spell.mana_cost is not None and unit.spell.mana_cost > 0:
                    skill_stats.append(f"Mana: {unit.spell.mana_cost}")
                    
            if hasattr(unit.spell, 'range') and unit.spell.range is not None:
                skill_stats.append(f"Range: {unit.spell.range}")
                
            if skill_stats:
                lines.append(f"  [{' | '.join(skill_stats)}]")
        
        return '\\n'.join(lines)
    
    def create_item_tooltip(self, item):
        lines = [
            f"{item.name}",
            f"Cost: {item.cost} gold",
            ""
        ]
        
        if hasattr(item, 'description') and item.description:
            lines.append(item.description)
            lines.append("")
            
        if hasattr(item, 'stats') and item.stats:
            lines.append("BONUSES:")
            for stat, value in item.stats.items():
                stat_name = stat.replace('_', ' ').title()
                if value > 0:
                    lines.append(f"• +{value} {stat_name}")
                else:
                    lines.append(f"• {value} {stat_name}")
                    
        return '\\n'.join(lines)
    
    def create_ability_tooltip(self, skill_name):
        """Create tooltip for abilities in the upgrade shop"""
        if not self.selected_unit:
            return ""
            
        skill = self.game.create_skill(skill_name)
        if not skill:
            return ""
            
        cost = self.selected_unit.get_passive_skill_cost(skill_name)
        display_name = skill_name.replace("_", " ").title()
        
        lines = [
            f"{display_name}",
            f"Cost: {cost} gold",
            ""
        ]
        
        if hasattr(skill, 'description') and skill.description:
            lines.append(skill.description)
            lines.append("")
            
        # Add any skill-specific stats or effects
        if hasattr(skill, 'damage') and skill.damage:
            lines.append(f"Damage: {skill.damage}")
        if hasattr(skill, 'range') and skill.range:
            lines.append(f"Range: {skill.range}")
        if hasattr(skill, 'cooldown_time') and skill.cooldown_time:
            lines.append(f"Cooldown: {skill.cooldown_time}s")
            
        return '\\n'.join(lines)


if __name__ == "__main__":
    ui = PyUI()
    ui.run()