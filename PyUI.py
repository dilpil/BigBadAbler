import pygame
import sys
import math
from enum import Enum
from game import Game, GamePhase, GameMode

class ShopType(Enum):
    NONE = "none"
    UNIT = "unit"

from content.unit_registry import create_unit, get_available_units, get_unit_cost
from unit import UnitType
from content.augments import generate_augment_shop, CharacterShopEntry, ItemShopEntry
from visual_effects import EffectManager
from visual_effect import VisualEffectType
from constants import FPS
from paths import resource_path

class PyUI:
    def __init__(self):
        pygame.init()
        self.width = 1400
        self.height = 900
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("BigBadAbler - Autobattler")
        
        # Initialize sound system
        pygame.mixer.init()
        self.load_sounds()
        
        self.clock = pygame.time.Clock()
        self.fps = FPS
        
        self.game = Game(GameMode.ASYNC)
        self.game.ui = self  # Allow game to access UI for sound effects
        
        self.tile_size = 75  # Increased from 60 to make units larger
        # Recalculate board position for 8x8 grid with 75px tiles
        board_width = 8 * 75  # 600px
        board_height = 8 * 75  # 600px
        self.board_x = (self.width - board_width) // 2  # 400px for 1400px screen
        self.board_y = (self.height - board_height) // 2 - 50  # Shift up slightly to leave room for UI
        
        self.selected_unit = None
        self.dragging_unit = None
        self.drag_offset = (0, 0)
        
        # Triple speed when tilde key is held
        self.triple_speed = False
        
        self.colors = {
            'background': (20, 0, 40),
            'board_bg': (40, 20, 60),
            'tile_player': (60, 30, 80),
            'tile_enemy': (80, 30, 60),
            'tile_hover': (100, 50, 120),
            'tile_border': (100, 50, 150),
            'player_border': (100, 255, 100),
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
            'sun_spirit': (255, 200, 50),
            'crazed_thornhound': (200, 50, 50),
            'pillar_of_bones': (150, 130, 100),
            'water_nymph': (100, 180, 255),
            'big_lips': (180, 100, 255),
            'oakenheart': (80, 150, 50),
            'imp_torturer': (255, 80, 30),
            'mass_of_tentacles': (120, 50, 180),
            'flame_maiden': (255, 120, 60),
            'red_wyrm': (220, 40, 40),
            'void_knight': (80, 120, 255),
            'blood_ogre': (180, 60, 60),
            'skeleton': (150, 150, 150),
            'panel_bg': (30, 10, 50),
            'panel_border': (100, 50, 150),
            'panel_flash_red': (255, 50, 50),
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

        # Dynamic tooltip tracking
        self.tooltip_unit = None
        self.tooltip_item = None
        self.tooltip_augment = None
        self.tooltip_skill = None
        self.tooltip_type = None

        self.shop_hover_unit = None
        self.shop_hover_ability = None
        self.shop_flash_timer = 0
        self.shop_flash_duration = 0.3
        self.selected_item = None
        self.selected_item_source_unit = None  # Track which unit an item is being moved from
        self.dragging_item = None  # Item currently being dragged
        self.dragging_item_source_unit = None  # Unit the dragged item came from (None = backpack)
        self.backpack_slots = []  # List of (rect, item) for click detection

        # Shop entry selection / dragging
        self.selected_shop_entry = None  # The shop entry being placed/applied
        self.selected_shop_entry_index = None  # Index in augment_shop
        self.dragging_shop_entry = None  # Shop entry currently being dragged
        self.dragging_shop_entry_index = None  # Its index in augment_shop
        self.hovered_tile = None  # (x, y) of tile being hovered over
        self.effect_manager = EffectManager()
        
        # Flash effect for invalid augment clicks
        self.augment_panel_flash_timer = 0
        self.augment_panel_flash_duration = 0.3  # Flash for 0.3 seconds
        self.shop_item_flash_index = None  # Index of shop item to flash red
        self.shop_item_flash_timer = 0
        
        # UI-only smooth movement tracking
        self.unit_visual_positions = {}  # unit_id -> (visual_x, visual_y, target_x, target_y, progress, duration)
        self.movement_duration = 0.3
        
        # Initialize the game after all attributes are set
        self.init_game()
    
    def load_sounds(self):
        """Load all sound effects"""
        self.sound_muted = True  # Set to False to enable sounds
        try:
            self.sounds = {
                'death': pygame.mixer.Sound(resource_path('soundFX/death_5.wav')),
                'hit': pygame.mixer.Sound(resource_path('soundFX/hit_4.wav')),
                'spell': pygame.mixer.Sound(resource_path('soundFX/sorcery_ally.wav')),
                'buy': pygame.mixer.Sound(resource_path('soundFX/menu_confirm.wav')),
                'shop_close': pygame.mixer.Sound(resource_path('soundFX/menu_abort.wav'))
            }
        except pygame.error as e:
            print(f"Error loading sounds: {e}")
            self.sounds = {}

    def play_sound(self, sound_name):
        """Play a sound effect"""
        if self.sound_muted:
            return
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def init_game(self):
        self.game.available_units = get_available_units()
        self.game.available_augments = generate_augment_shop()
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
            
            # Check if tilde key is currently held down
            keys = pygame.key.get_pressed()
            self.triple_speed = keys[pygame.K_BACKQUOTE]  # Tilde/backtick key
            
            # Update game (possibly multiple times for triple speed)
            if self.triple_speed:
                # Run 3 updates per frame for triple speed
                for _ in range(3):
                    self.update(dt)
            else:
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
        # During POST_COMBAT phase, any key press or mouse click ends it
        if self.game.phase == GamePhase.POST_COMBAT:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.game.end_combat()
                return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_click(event.pos)
            elif event.button == 3:
                self.handle_right_click(event.pos)
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_shop_entry:
                self.handle_shop_entry_drop(event.pos)
            elif event.button == 1 and self.dragging_item:
                self.handle_item_drop(event.pos)
            elif event.button == 1 and self.dragging_unit:
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
                # Cancel drags/selections or close shop
                if self.dragging_shop_entry:
                    self.dragging_shop_entry = None
                    self.dragging_shop_entry_index = None
                elif self.dragging_item:
                    self.dragging_item = None
                    self.dragging_item_source_unit = None
                elif self.selected_item:
                    self.selected_item = None
                    self.selected_item_source_unit = None
                elif self.shop_open != ShopType.NONE:
                    self.shop_open = ShopType.NONE
                                    
    def handle_click(self, pos):
        x, y = pos

        # Check backpack click (for selecting items from backpack)
        if self.game.phase == GamePhase.SHOPPING:
            for slot_rect, item in self.backpack_slots:
                if slot_rect.collidepoint(pos):
                    if item:
                        # Start dragging the item from backpack
                        self.dragging_item = item
                        self.dragging_item_source_unit = None  # From backpack
                        return

        if self.shop_open != ShopType.NONE:
            if not self.is_click_in_shop(pos):
                self.shop_open = ShopType.NONE
                self.play_sound('shop_close')
            else:
                self.handle_shop_click(pos)
            return
            
        # Check item shop click
        if self.game.phase == GamePhase.SHOPPING and y > self.height - 150:
            self.handle_augment_shop_click(pos)
            return
            
        grid_x, grid_y = self.screen_to_grid(x, y)
        if 0 <= grid_x < 8 and 0 <= grid_y < 8:
            unit = self.game.board.get_unit_at(grid_x, grid_y)
            if unit and unit.team == "player" and self.game.phase == GamePhase.SHOPPING:
                # Check if clicking on a unit's item square to start dragging it
                item_clicked = self._get_item_at_pos(unit, x, y)
                if item_clicked:
                    self.dragging_item = item_clicked
                    self.dragging_item_source_unit = unit
                    return

                # Start dragging the unit
                tile_x = self.board_x + unit.x * self.tile_size
                tile_y = self.board_y + unit.y * self.tile_size
                self.dragging_unit = unit
                self.drag_offset = (x - tile_x, y - tile_y)
                self.selected_unit = unit
            elif not unit and grid_x < 4 and self.game.phase == GamePhase.SHOPPING:
                pass  # Empty tile - units are placed via drag and drop from shop
        else:
            if self.game.phase == GamePhase.SHOPPING:
                self.selected_unit = None
                
    def handle_right_click(self, pos):
        # Right-click on a unit's item square to unequip to backpack
        if self.game.phase == GamePhase.SHOPPING:
            grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
            if 0 <= grid_x < 8 and 0 <= grid_y < 8:
                unit = self.game.board.get_unit_at(grid_x, grid_y)
                if unit and unit.team == "player":
                    item_clicked = self._get_item_at_pos(unit, pos[0], pos[1])
                    if item_clicked and item_clicked in unit.items:
                        unit.remove_item(item_clicked)
                        self.game.player_team.unequipped_items.append(item_clicked)
                        self.game.add_message(f"Unequipped {item_clicked.name} from {unit.name}")
                        return

        # Cancel any drags/selections on right click
        if self.dragging_shop_entry:
            self.dragging_shop_entry = None
            self.dragging_shop_entry_index = None
        if self.selected_shop_entry:
            self.selected_shop_entry = None
            self.selected_shop_entry_index = None

        # Deselect unit on right click
        if self.selected_unit:
            self.selected_unit = None
            return

        # Close shop if it's open
        if self.shop_open != ShopType.NONE:
            self.shop_open = ShopType.NONE
            self.play_sound('shop_close')
            return

        grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
        if 0 <= grid_x < 8 and 0 <= grid_y < 8:
            unit = self.game.board.get_unit_at(grid_x, grid_y)
            if unit and unit.team == "player" and self.game.phase == GamePhase.SHOPPING:
                # Right-click on unit just selects it
                self.selected_unit = unit
                
    def handle_drop(self, pos):
        if not self.dragging_unit:
            return

        grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
        if 0 <= grid_x < 8 and 0 <= grid_y < 8:
            # Only allow player units on left side (x = 0-3)
            if self.dragging_unit.team == "player" and grid_x >= 4:
                self.dragging_unit = None
                return

            # Only allow enemy units on right side (x = 4-7)
            if self.dragging_unit.team == "enemy" and grid_x < 4:
                self.dragging_unit = None
                return

            occupant = self.game.board.get_unit_at(grid_x, grid_y)
            if occupant and occupant != self.dragging_unit and occupant.team == self.dragging_unit.team:
                # Swap the two units
                old_x, old_y = self.dragging_unit.x, self.dragging_unit.y
                # Remove both from board
                self.game.board.remove_unit(self.dragging_unit)
                self.game.board.remove_unit(occupant)
                # Place them in swapped positions
                self.game.board.add_unit(self.dragging_unit, grid_x, grid_y, self.dragging_unit.team)
                self.game.board.add_unit(occupant, old_x, old_y, occupant.team)
                if self.game.phase == GamePhase.SHOPPING:
                    self.dragging_unit.original_x = grid_x
                    self.dragging_unit.original_y = grid_y
                    occupant.original_x = old_x
                    occupant.original_y = old_y
                # Clear visual positions for both so they snap
                for uid in [self.dragging_unit.id, occupant.id]:
                    if uid in self.unit_visual_positions:
                        del self.unit_visual_positions[uid]
            elif not occupant:
                # Move to empty tile
                unit_id = self.dragging_unit.id
                if unit_id in self.unit_visual_positions:
                    del self.unit_visual_positions[unit_id]
                self.game.board.move_unit(self.dragging_unit, grid_x, grid_y)
                if self.game.phase == GamePhase.SHOPPING and self.dragging_unit.team == "player":
                    self.dragging_unit.original_x = grid_x
                    self.dragging_unit.original_y = grid_y

        self.dragging_unit = None

    def _get_item_at_pos(self, unit, screen_x, screen_y):
        """Check if a screen position hits one of a unit's item squares."""
        if not unit.items:
            return None
        # Get unit's visual position
        unit_id = unit.id
        if unit_id in self.unit_visual_positions:
            vx = self.unit_visual_positions[unit_id]['visual_x']
            vy = self.unit_visual_positions[unit_id]['visual_y']
        else:
            vx = float(unit.x)
            vy = float(unit.y)
        ux = self.board_x + vx * self.tile_size
        uy = self.board_y + vy * self.tile_size
        for i, item in enumerate(unit.items[:3]):
            item_x = ux + 2
            item_y = uy + 4 + i * 16
            if item_x <= screen_x <= item_x + 14 and item_y <= screen_y <= item_y + 14:
                return item
        return None

    def handle_item_drop(self, pos):
        """Handle dropping an item being dragged."""
        if not self.dragging_item:
            return

        item = self.dragging_item
        source_unit = self.dragging_item_source_unit

        # Check if dropped on a player unit
        grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
        if 0 <= grid_x < 8 and 0 <= grid_y < 8:
            target_unit = self.game.board.get_unit_at(grid_x, grid_y)
            if target_unit and target_unit.team == "player" and len(target_unit.items) < 3:
                if target_unit != source_unit:
                    # Move item to target unit
                    if source_unit:
                        source_unit.remove_item(item)
                    else:
                        self.game.player_team.unequipped_items.remove(item)
                    target_unit.add_item(item)
                    src_name = source_unit.name if source_unit else "backpack"
                    self.game.add_message(f"Moved {item.name} from {src_name} to {target_unit.name}")
                    self.dragging_item = None
                    self.dragging_item_source_unit = None
                    return

        # Check if dropped on backpack area
        backpack_rect = self._get_backpack_panel_rect()
        if backpack_rect and backpack_rect.collidepoint(pos):
            if source_unit:
                source_unit.remove_item(item)
                self.game.player_team.unequipped_items.append(item)
                self.game.add_message(f"Unequipped {item.name} to backpack")
            # If already from backpack, just cancel
            self.dragging_item = None
            self.dragging_item_source_unit = None
            return

        # Dropped elsewhere - return item to source
        self.dragging_item = None
        self.dragging_item_source_unit = None

    def handle_shop_entry_drop(self, pos):
        """Handle dropping a shop entry (character or item) being dragged."""
        entry = self.dragging_shop_entry
        index = self.dragging_shop_entry_index
        self.dragging_shop_entry = None
        self.dragging_shop_entry_index = None

        if not entry or index is None:
            return

        # Verify entry is still in the shop at the expected index
        if index >= len(self.game.augment_shop) or self.game.augment_shop[index] is not entry:
            return

        if isinstance(entry, CharacterShopEntry):
            # Drop character on an empty player-side tile
            grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
            if 0 <= grid_x < 4 and 0 <= grid_y < 8:
                if not self.game.board.get_unit_at(grid_x, grid_y):
                    if self.game.purchase_character_entry(index, grid_x, grid_y):
                        new_unit = self.game.board.get_unit_at(grid_x, grid_y)
                        if new_unit:
                            self.selected_unit = new_unit

        elif isinstance(entry, ItemShopEntry):
            # Drop item on a player unit to purchase and equip directly
            grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
            if 0 <= grid_x < 8 and 0 <= grid_y < 8:
                target_unit = self.game.board.get_unit_at(grid_x, grid_y)
                if target_unit and target_unit.team == "player" and len(target_unit.items) < 3:
                    item = self.game.purchase_item_entry(index)
                    if item:
                        self.game.player_team.unequipped_items.remove(item)
                        target_unit.add_item(item)
                        self.game.add_message(f"Equipped {item.name} to {target_unit.name}")
                    return

            # Drop item on backpack area or elsewhere -> purchase to backpack
            self.game.purchase_item_entry(index)

    def _get_backpack_panel_rect(self):
        """Return the rect for the backpack panel area."""
        if self.game.phase != GamePhase.SHOPPING:
            return None
        shop_y = self.height - 160
        return pygame.Rect(10, shop_y + 5, 220, 150)

    def handle_mouse_motion(self, pos):
        # Reset shop hover state
        self.shop_hover_unit = None
        self.shop_hover_ability = None
        
        # Clear all tooltip references
        self.tooltip_unit = None
        self.tooltip_item = None
        self.tooltip_augment = None
        self.tooltip_skill = None
        self.tooltip_type = None
        self.tooltip = None
        
        # Check if we're in a shop
        if self.shop_open == ShopType.UNIT:
            hover_unit = self.get_shop_hover_unit(pos)
            if hover_unit:
                self.shop_hover_unit = hover_unit
                # Store reference for dynamic tooltip generation
                unit_instance = create_unit(hover_unit)
                self.tooltip_unit = unit_instance
                self.tooltip_type = "shop_unit"
                return
            else:
                return

        grid_x, grid_y = self.screen_to_grid(pos[0], pos[1])
        if 0 <= grid_x < 8 and 0 <= grid_y < 8:
            # Track hovered tile for plus sign indicator
            self.hovered_tile = (grid_x, grid_y)
            
            unit = self.game.board.get_unit_at(grid_x, grid_y)
            if unit:
                # Store unit reference for dynamic tooltip generation
                self.tooltip_unit = unit
                self.tooltip_type = "unit"
            else:
                pass  # No tooltip
        else:
            # Clear hovered tile when mouse leaves board
            self.hovered_tile = None
            
            # Check owned augments tooltip (left side panel)
            if self.game.player_team.augments:
                for augment in self.game.player_team.augments:
                    if hasattr(augment, 'ui_rect') and augment.ui_rect.collidepoint(pos):
                        self.tooltip_augment = augment
                        self.tooltip_type = "augment"
                        return
            
            # Check enemy augments tooltip (right side panel)
            if self.game.enemy_team.augments:
                for augment in self.game.enemy_team.augments:
                    if hasattr(augment, 'ui_rect') and augment.ui_rect.collidepoint(pos):
                        self.tooltip_augment = augment
                        self.tooltip_type = "augment"
                        return
            
            # Check shop tooltip
            if self.game.phase == GamePhase.SHOPPING and pos[1] > self.height - 150:
                # Calculate centered position
                augment_width = 80
                augment_spacing = 8
                total_width = len(self.game.augment_shop) * augment_width + (len(self.game.augment_shop) - 1) * augment_spacing
                start_x = (self.width - total_width) // 2

                # Check which shop entry is hovered
                for i, entry in enumerate(self.game.augment_shop):
                    aug_x = start_x + i * (augment_width + augment_spacing)
                    if aug_x <= pos[0] <= aug_x + augment_width:
                        # Handle different entry types for tooltips
                        if isinstance(entry, CharacterShopEntry):
                            self.tooltip_unit = create_unit(entry.unit_type)
                            self.tooltip_type = "shop_unit"
                        elif isinstance(entry, ItemShopEntry):
                            # Create temp item for tooltip
                            self.tooltip_item = entry.create_item()
                            self.tooltip_type = "item"
                        else:
                            self.tooltip_augment = entry
                            self.tooltip_type = "augment"
                        return

            # Check backpack tooltip
            if self.game.phase == GamePhase.SHOPPING:
                for slot_rect, item in self.backpack_slots:
                    if item and slot_rect.collidepoint(pos):
                        self.tooltip_item = item
                        self.tooltip_type = "item"
                        return
                
    def handle_shop_click(self, pos):
        if self.shop_open == ShopType.UNIT:
            self._handle_unit_shop_click(pos)
    
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
                # Try to purchase the unit
                success = self.game.purchase_unit(unit_type, self.shop_position[0], self.shop_position[1])
                if success:
                    # Purchase successful - close shop
                    self.shop_open = ShopType.NONE
                else:
                    # Purchase failed - flash red and keep shop open
                    self.shop_flash_timer = self.shop_flash_duration
                return

    def handle_augment_shop_click(self, pos):
        if self.game.phase != GamePhase.SHOPPING:
            return

        shop_y = self.height - 160

        # Check reroll button click
        reroll_x = 250
        reroll_y = shop_y + 120
        if reroll_x <= pos[0] <= reroll_x + 100 and reroll_y <= pos[1] <= reroll_y + 30:
            if self.game.reroll_shop(20):
                # Clear any selection/drag
                self.selected_shop_entry = None
                self.selected_shop_entry_index = None
                self.dragging_shop_entry = None
                self.dragging_shop_entry_index = None
            # If can't afford reroll, just do nothing
            return

        # Calculate centered position for shop items
        augment_width = 80
        augment_spacing = 8
        total_width = len(self.game.augment_shop) * augment_width + (len(self.game.augment_shop) - 1) * augment_spacing
        start_x = (self.width - total_width) // 2

        # Check which shop entry was clicked
        for i, entry in enumerate(self.game.augment_shop):
            aug_x = start_x + i * (augment_width + augment_spacing)
            if aug_x <= pos[0] <= aug_x + augment_width:
                from augment import UnitAugment, PassiveAugment

                if self.game.gold >= entry.cost:
                    if isinstance(entry, (CharacterShopEntry, ItemShopEntry)):
                        # Start dragging the shop entry (purchase happens on drop)
                        self.dragging_shop_entry = entry
                        self.dragging_shop_entry_index = i

                    elif isinstance(entry, UnitAugment):
                        if self.game.purchase_augment(i):
                            if self.game.board.player_units:
                                newest_unit = self.game.board.player_units[-1]
                                self.selected_unit = newest_unit
                                self.game.add_message(f"Selected {newest_unit.name}")

                    else:
                        self.game.purchase_augment(i)
                else:
                    if not isinstance(entry, PassiveAugment):
                        self.shop_item_flash_index = i
                        self.shop_item_flash_timer = self.augment_panel_flash_duration
                break
            
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

    def is_click_in_shop(self, pos):
        if self.shop_open == ShopType.UNIT:
            shop_width = 480
            shop_height = 480
            shop_x = self.width // 2 - shop_width // 2
            shop_y = self.height // 2 - shop_height // 2
            return (shop_x <= pos[0] <= shop_x + shop_width and
                   shop_y <= pos[1] <= shop_y + shop_height)
        return False
        
    def screen_to_grid(self, x, y):
        grid_x = (x - self.board_x) // self.tile_size
        grid_y = (y - self.board_y) // self.tile_size
        return grid_x, grid_y
    
    def _blend_colors(self, color1, color2, blend_factor):
        """Blend two colors together. blend_factor 0 = color1, 1 = color2"""
        r = int(color1[0] * (1 - blend_factor) + color2[0] * blend_factor)
        g = int(color1[1] * (1 - blend_factor) + color2[1] * blend_factor) 
        b = int(color1[2] * (1 - blend_factor) + color2[2] * blend_factor)
        return (r, g, b)
        
    def update(self, dt):
        # Update shop flash timer
        if self.shop_flash_timer > 0:
            self.shop_flash_timer -= dt
        
        # Update augment panel flash timer
        if self.augment_panel_flash_timer > 0:
            self.augment_panel_flash_timer -= dt

        # Update shop item flash timer
        if self.shop_item_flash_timer > 0:
            self.shop_item_flash_timer -= dt
            if self.shop_item_flash_timer <= 0:
                self.shop_item_flash_index = None

        # Track unit position changes for smooth movement
        if self.game.phase in [GamePhase.COMBAT, GamePhase.POST_COMBAT]:
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
            # If phase changed to shopping, clear visual positions
            if prev_phase in [GamePhase.COMBAT, GamePhase.POST_COMBAT] and self.game.phase == GamePhase.SHOPPING:
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
        self.draw_visual_effects()
        self.draw_units()
        self.draw_projectiles()
        self.draw_text_floaters()
        self.draw_ui()
        self.draw_owned_augments()
        self.draw_backpack()
        self.draw_enemy_augments()
        self.effect_manager.draw(self.screen, self.fonts['small'])
        
        if self.shop_open != ShopType.NONE:
            self.draw_shop()
            
        if self.tooltip_type or self.tooltip:
            self.draw_tooltip()
            
        if self.dragging_shop_entry:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self._draw_dragged_shop_entry(mouse_x, mouse_y)

        if self.dragging_item:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self._draw_dragged_item(mouse_x, mouse_y)

        if self.dragging_unit:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.draw_unit_at(self.dragging_unit, mouse_x - self.drag_offset[0],
                            mouse_y - self.drag_offset[1], alpha=128)
        
        # Draw victory/defeat banner during post-combat
        if self.game.phase == GamePhase.POST_COMBAT:
            self.draw_combat_result_banner()
        
        # Draw triple speed indicator
        if self.triple_speed:
            self.draw_triple_speed_indicator()
            
        pygame.display.flip()
    
    def draw_triple_speed_indicator(self):
        """Draw a visual indicator that triple speed is active"""
        # Draw in top-right corner
        indicator_text = "3X SPEED"
        text_surface = self.fonts['large'].render(indicator_text, True, (255, 255, 0))  # Yellow text
        
        # Position in top-right corner with some padding
        text_rect = text_surface.get_rect()
        text_rect.topright = (self.width - 20, 20)
        
        # Draw background rectangle
        bg_rect = text_rect.inflate(20, 10)  # Add padding around text
        pygame.draw.rect(self.screen, (100, 50, 0), bg_rect)  # Dark orange background
        pygame.draw.rect(self.screen, (255, 255, 0), bg_rect, 2)  # Yellow border
        
        # Draw the text
        self.screen.blit(text_surface, text_rect)
        
    def draw_board(self):
        board_width = 8 * self.tile_size
        board_height = 8 * self.tile_size

        # Draw grid lines (9 lines for 8x8 grid)
        for i in range(9):
            # Vertical lines
            x = self.board_x + i * self.tile_size
            pygame.draw.line(self.screen, self.colors['tile_border'],
                           (x, self.board_y), (x, self.board_y + board_height), 1)
            # Horizontal lines
            y = self.board_y + i * self.tile_size
            pygame.draw.line(self.screen, self.colors['tile_border'],
                           (self.board_x, y), (self.board_x + board_width, y), 1)

        # Draw middle divider
        mid_x = self.board_x + 4 * self.tile_size
        pygame.draw.line(self.screen, (128, 0, 255),
                       (mid_x, self.board_y), (mid_x, self.board_y + board_height), 5)
                               
    
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
                
        # Draw unit square - always black background
        unit_color = self.colors.get(unit.unit_type.value, (100, 100, 100))
        background_color = (0, 0, 0)

        # Apply flash effect to background
        if unit.flash_timer > 0 and unit.flash_color:
            if unit.state.value == "casting":  # Continuous oscillating glow during casting
                cast_progress = unit.cast_timer / unit.cast_time if unit.cast_time > 0 else 0
                oscillation = math.sin(unit.cast_timer * 8) * 0.5 + 0.5
                base_intensity = 0.3 + (cast_progress * 0.4)
                flash_intensity = min(1.0, base_intensity + (oscillation * 0.3))
            else:
                flash_intensity = unit.flash_timer / unit.flash_duration

            background_color = tuple(
                int(background_color[i] * (1 - flash_intensity) + unit.flash_color[i] * flash_intensity)
                for i in range(3)
            )

        s = pygame.Surface((self.tile_size - 4, self.tile_size - 4))
        s.fill(background_color)
        s.set_alpha(alpha)
        self.screen.blit(s, (x + offset_x + 2, y + offset_y + 2))

        # Draw unit letter with unit color
        letter = unit.unit_type.value[0].upper()
        text = self.fonts['large'].render(letter, True, unit_color)
        text_rect = text.get_rect(center=(x + offset_x + self.tile_size // 2,
                                         y + offset_y + self.tile_size // 2 - 5))
        self.screen.blit(text, text_rect)

        # Draw border
        border_color = self.colors['player_border'] if unit.team == "player" else self.colors['enemy_border']
        pygame.draw.rect(self.screen, border_color,
                        (x + offset_x + 2, y + offset_y + 2, self.tile_size - 4, self.tile_size - 4), 3)

        # Draw selection highlight if this unit is selected
        if self.selected_unit == unit and self.game.phase == GamePhase.SHOPPING:
            selection_color = (255, 255, 0)  # Yellow highlight
            pygame.draw.rect(self.screen, selection_color,
                            (x + offset_x, y + offset_y, self.tile_size, self.tile_size), 4)
        
        # Draw items as squares stacked vertically on left side
        if unit.items:
            for i, item in enumerate(unit.items[:3]):  # Max 3 items
                item_x = x + offset_x + 2  # Left side
                item_y = y + offset_y + 4 + i * 16  # Stacked vertically
                item_color = self.get_item_color(item.name)
                
                # Draw colored square (slightly larger)
                pygame.draw.rect(self.screen, item_color, (item_x, item_y, 14, 14))
                pygame.draw.rect(self.screen, (255, 255, 255), (item_x, item_y, 14, 14), 1)
                
                # Draw item letter
                letter = self.get_item_letter(item.name)
                text = self.fonts['tiny'].render(letter, True, self.colors['text'])
                text_rect = text.get_rect(center=(item_x + 7, item_y + 7))
                self.screen.blit(text, text_rect)
        
        # Draw status effects as circles above HP bar
        if unit.status_effects:
            # Position them just above the HP bar
            status_base_y = y + offset_y + self.tile_size - 28  # Above HP bar
            for i, status in enumerate(unit.status_effects[:6]):  # Max 6 shown
                status_x = x + offset_x + 8 + i * 12  # Horizontal spacing
                status_y = status_base_y
                status_color = (200, 100, 255) if "buff" in status.name.lower() else (255, 100, 100)
                
                # Draw circle
                pygame.draw.circle(self.screen, status_color, (status_x + 5, status_y + 5), 5)
                pygame.draw.circle(self.screen, (255, 255, 255), (status_x + 5, status_y + 5), 5, 1)
                
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
        
        # Draw HP bar (moved up to not cover border)
        hp_bar_y = y + offset_y + self.tile_size - 16
        bar_x = x + offset_x + 4
        bar_width = self.tile_size - 8
        pygame.draw.rect(self.screen, self.colors['hp_bar_bg'],
                        (bar_x, hp_bar_y, bar_width, 4))

        # Draw orange damage drain portion (from hp to old_cur_hp)
        if hasattr(unit, 'old_cur_hp') and unit.old_cur_hp > unit.hp:
            old_hp_width = int(bar_width * (unit.old_cur_hp / unit.max_hp))
            hp_width = int(bar_width * (unit.hp / unit.max_hp))
            if old_hp_width > hp_width:
                pygame.draw.rect(self.screen, (255, 150, 50),
                                (bar_x + hp_width, hp_bar_y, old_hp_width - hp_width, 4))

        # Draw light green heal fill portion (from old_cur_hp to hp)
        if hasattr(unit, 'old_cur_hp') and unit.old_cur_hp < unit.hp:
            old_hp_width = int(bar_width * (unit.old_cur_hp / unit.max_hp))
            hp_width = int(bar_width * (unit.hp / unit.max_hp))
            if hp_width > old_hp_width:
                pygame.draw.rect(self.screen, (150, 255, 150),
                                (bar_x + old_hp_width, hp_bar_y, hp_width - old_hp_width, 4))

        # Draw current HP bar (green) - use min of hp and old_cur_hp for visual
        visual_hp = min(unit.hp, unit.old_cur_hp) if hasattr(unit, 'old_cur_hp') else unit.hp
        hp_width = int(bar_width * (visual_hp / unit.max_hp))
        if hp_width > 0:
            pygame.draw.rect(self.screen, self.colors['hp_bar'],
                            (bar_x, hp_bar_y, hp_width, 4))
                            
        # Draw MP bar (shows spell mana) - moved up
        mp_bar_y = y + offset_y + self.tile_size - 10
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
            from unit import DamageType, DAMAGE_TYPE_COLORS
            color = (255, 255, 100)  # Default yellow
            if hasattr(projectile, 'damage_types') and projectile.damage_types:
                color = DAMAGE_TYPE_COLORS.get(projectile.damage_types[0], color)
            elif hasattr(projectile, 'damage_type') and projectile.damage_type:
                try:
                    dt = DamageType(projectile.damage_type)
                    color = DAMAGE_TYPE_COLORS.get(dt, color)
                except ValueError:
                    pass
                
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
        
        for i, (text, x) in enumerate(stats):
            # Flash lives counter on defeat during post-combat
            if i == 1 and self.game.phase == GamePhase.POST_COMBAT and self.game.combat_result == "defeat":
                # Create flashing effect
                flash = int(self.game.post_combat_timer * 4) % 2
                color = self.colors['enemy_border'] if flash else self.colors['text']
                rendered = self.fonts['medium'].render(text, True, color)
            else:
                rendered = self.fonts['medium'].render(text, True, self.colors['text'])
            self.screen.blit(rendered, (x, y))
            
        # Phase indicator
        if self.game.phase == GamePhase.SHOPPING:
            phase_text = "SHOPPING PHASE"
            phase_color = self.colors['player_border']
        elif self.game.phase == GamePhase.POST_COMBAT:
            phase_text = "COMBAT ENDED"
            phase_color = self.colors['text']
        else:
            phase_text = "COMBAT PHASE"
            phase_color = self.colors['enemy_border']
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
            
            # Item shop panel
            shop_y = self.height - 160
            
            # Apply flash effect if timer is active
            if self.augment_panel_flash_timer > 0:
                # Calculate flash intensity (fade out over time)
                flash_intensity = self.augment_panel_flash_timer / self.augment_panel_flash_duration
                # Blend between normal panel color and red based on intensity
                panel_color = self._blend_colors(self.colors['panel_bg'], self.colors['panel_flash_red'], flash_intensity)
                border_color = self._blend_colors(self.colors['panel_border'], (255, 100, 100), flash_intensity)
            else:
                panel_color = self.colors['panel_bg']
                border_color = self.colors['panel_border']
            
            pygame.draw.rect(self.screen, panel_color, 
                           (0, shop_y, self.width, 160))
            pygame.draw.line(self.screen, border_color, 
                           (0, shop_y), (self.width, shop_y), 3)
            
            # Shop title and reroll (positioned to the right of backpack)
            text = self.fonts['medium'].render("SHOP", True, self.colors['text'])
            self.screen.blit(text, (250, shop_y + 10))

            # Draw reroll button
            reroll_cost = 20
            can_reroll = self.game.gold >= reroll_cost
            reroll_x = 250
            reroll_y = shop_y + 120
            reroll_color = self.colors['button'] if can_reroll else self.colors['button_disabled']
            pygame.draw.rect(self.screen, reroll_color, (reroll_x, reroll_y, 100, 30))
            pygame.draw.rect(self.screen, self.colors['panel_border'], (reroll_x, reroll_y, 100, 30), 2)
            reroll_text = self.fonts['small'].render(f"Reroll {reroll_cost}g", True,
                                                     self.colors['text'] if can_reroll else (100, 100, 100))
            reroll_rect = reroll_text.get_rect(center=(reroll_x + 50, reroll_y + 15))
            self.screen.blit(reroll_text, reroll_rect)

            # Draw shop items (centered) - smaller for 10 items
            augment_width = 80  # Smaller width for 10 items
            augment_height = 70
            augment_spacing = 8
            total_width = len(self.game.augment_shop) * augment_width + (len(self.game.augment_shop) - 1) * augment_spacing
            start_x = (self.width - total_width) // 2

            for i, entry in enumerate(self.game.augment_shop):
                x = start_x + i * (augment_width + augment_spacing)
                y = shop_y + 45

                # Determine entry type and display properties
                can_afford = self.game.gold >= entry.cost
                is_selected = (self.selected_shop_entry_index == i or
                               self.dragging_shop_entry_index == i)

                # Draw selection glow if selected
                if is_selected:
                    for j in range(3):
                        glow_alpha = 150 - (j * 40)
                        glow_surface = pygame.Surface((augment_width + 6 + j * 4, augment_height + 6 + j * 4))
                        glow_surface.fill((255, 200, 0))
                        glow_surface.set_alpha(glow_alpha)
                        self.screen.blit(glow_surface, (x - 3 - j * 2, y - 3 - j * 2))

                color = self.colors['button'] if can_afford else self.colors['button_disabled']
                pygame.draw.rect(self.screen, color, (x, y, augment_width, augment_height))
                border_color = (255, 200, 0) if is_selected else self.colors['panel_border']
                border_width = 3 if is_selected else 2
                pygame.draw.rect(self.screen, border_color, (x, y, augment_width, augment_height), border_width)

                # Determine entry type colors and letter
                from augment import PassiveAugment, UnitAugment

                if isinstance(entry, CharacterShopEntry):
                    unit_type_name = entry.unit_type.name.lower()
                    aug_color = self.colors.get(unit_type_name, (100, 200, 100))
                    aug_letter = entry.unit_type.name[0]
                elif isinstance(entry, ItemShopEntry):
                    aug_color = (100, 150, 200)  # Blue for items
                    aug_letter = 'I'
                elif isinstance(entry, PassiveAugment):
                    aug_color = (150, 100, 200)  # Purple for passives
                    aug_letter = 'A'
                elif isinstance(entry, UnitAugment):
                    aug_color = (200, 150, 100)  # Gold for rare units
                    aug_letter = 'U'
                else:
                    aug_color = (150, 150, 150)
                    aug_letter = '?'

                item_size = 32
                item_x = x + (augment_width - item_size) // 2
                item_y = y + 6

                # Check if this item should flash red
                is_flashing = (self.shop_item_flash_index == i and self.shop_item_flash_timer > 0)
                if is_flashing:
                    flash_intensity = self.shop_item_flash_timer / self.augment_panel_flash_duration
                    flash_color = self._blend_colors(aug_color, (255, 50, 50), flash_intensity)
                else:
                    flash_color = aug_color

                # Apply transparency if can't afford
                if not can_afford:
                    s = pygame.Surface((item_size, item_size))
                    s.fill(flash_color)
                    s.set_alpha(100)
                    self.screen.blit(s, (item_x, item_y))
                else:
                    pygame.draw.rect(self.screen, flash_color, (item_x, item_y, item_size, item_size))

                # Draw type letter
                text_color = self.colors['text'] if can_afford else (100, 100, 100)
                text = self.fonts['small'].render(aug_letter, True, text_color)
                text_rect = text.get_rect(center=(item_x + item_size // 2, item_y + item_size // 2))
                self.screen.blit(text, text_rect)

                # Entry name below the square (truncate if too long)
                name = entry.name[:10] + '..' if len(entry.name) > 10 else entry.name
                text = self.fonts['tiny'].render(name, True, self.colors['text'])
                text_rect = text.get_rect(center=(x + augment_width // 2, y + 48))
                self.screen.blit(text, text_rect)

                # Cost
                text = self.fonts['tiny'].render(f"{entry.cost}g", True,
                                                 self.colors['text'] if can_afford else (100, 100, 100))
                text_rect = text.get_rect(center=(x + augment_width // 2, y + 60))
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
            
            # Draw messages - start from top without title
            y = log_y + 10
            for message in self.game.message_log[-7:]:
                text = self.fonts['small'].render(message, True, self.colors['text'])
                self.screen.blit(text, (log_x + 20, y))
                y += 20
                
    def draw_owned_augments(self):
        """Draw owned augments (non-item) stacked vertically on the left side"""
        # Filter to only non-item augments
        from augment import PassiveAugment, UnitAugment
        augments = [a for a in self.game.player_team.augments
                    if isinstance(a, (PassiveAugment, UnitAugment))]
        if not augments:
            return

        panel_width = 200
        panel_height = min(600, len(augments) * 55 + 40)
        panel_x = 20
        panel_y = 100

        panel_color = self.colors['panel_bg']
        border_color = self.colors['panel_border']

        pygame.draw.rect(self.screen, panel_color,
                        (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, border_color,
                        (panel_x, panel_y, panel_width, panel_height), 2)

        title_text = self.fonts['medium'].render("AUGMENTS", True, self.colors['text'])
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))

        for i, augment in enumerate(augments):
            augment_y = panel_y + 40 + i * 55
            augment_rect = pygame.Rect(panel_x + 10, augment_y, panel_width - 20, 50)
            augment.ui_rect = augment_rect

            bg_color = self.colors['button']
            pygame.draw.rect(self.screen, bg_color, augment_rect)
            pygame.draw.rect(self.screen, self.colors['panel_border'], augment_rect, 1)

            if isinstance(augment, PassiveAugment):
                aug_color = (150, 100, 200)
                aug_letter = 'P'
            elif isinstance(augment, UnitAugment):
                aug_color = (200, 150, 100)
                aug_letter = 'U'
            else:
                aug_color = (150, 150, 150)
                aug_letter = '?'

            icon_size = 30
            icon_x = augment_rect.x + 5
            icon_y = augment_rect.y + 10
            pygame.draw.rect(self.screen, aug_color, (icon_x, icon_y, icon_size, icon_size))

            letter_text = self.fonts['medium'].render(aug_letter, True, self.colors['text'])
            letter_rect = letter_text.get_rect(center=(icon_x + icon_size // 2, icon_y + icon_size // 2))
            self.screen.blit(letter_text, letter_rect)

            name = augment.name[:20] + '...' if len(augment.name) > 20 else augment.name
            name_text = self.fonts['small'].render(name, True, self.colors['text'])
            name_y = augment_rect.y + (augment_rect.height - name_text.get_height()) // 2
            self.screen.blit(name_text, (icon_x + icon_size + 10, name_y))
    
    def draw_backpack(self):
        """Draw the backpack panel in the bottom-left showing unequipped items."""
        if self.game.phase != GamePhase.SHOPPING:
            self.backpack_slots = []
            return

        panel_rect = self._get_backpack_panel_rect()
        if not panel_rect:
            return

        # Draw panel background
        pygame.draw.rect(self.screen, self.colors['panel_bg'], panel_rect)
        pygame.draw.rect(self.screen, self.colors['panel_border'], panel_rect, 2)

        # Title
        title = self.fonts['small'].render("BACKPACK", True, self.colors['text'])
        self.screen.blit(title, (panel_rect.x + 10, panel_rect.y + 5))

        # Draw item slots in a grid (5 columns, 3 rows = 15 max)
        slot_size = 36
        slot_spacing = 4
        cols = 5
        start_x = panel_rect.x + 10
        start_y = panel_rect.y + 25

        items = self.game.player_team.unequipped_items
        self.backpack_slots = []

        for i in range(15):  # 15 slots
            col = i % cols
            row = i // cols
            sx = start_x + col * (slot_size + slot_spacing)
            sy = start_y + row * (slot_size + slot_spacing)
            slot_rect = pygame.Rect(sx, sy, slot_size, slot_size)

            # Draw slot background
            if i < len(items):
                item = items[i]
                # Highlight if being dragged from here
                if self.dragging_item == item and self.dragging_item_source_unit is None:
                    pygame.draw.rect(self.screen, (60, 60, 30), slot_rect)
                else:
                    pygame.draw.rect(self.screen, (50, 30, 70), slot_rect)
                pygame.draw.rect(self.screen, (100, 150, 200), slot_rect, 2)

                # Draw item icon
                item_color = self.get_item_color(item.name)
                icon_rect = pygame.Rect(sx + 4, sy + 4, slot_size - 8, slot_size - 8)
                pygame.draw.rect(self.screen, item_color, icon_rect)

                # Item letter
                letter = self.get_item_letter(item.name)
                text = self.fonts['small'].render(letter, True, self.colors['text'])
                text_rect = text.get_rect(center=icon_rect.center)
                self.screen.blit(text, text_rect)

                self.backpack_slots.append((slot_rect, item))
            else:
                # Empty slot
                pygame.draw.rect(self.screen, (30, 15, 45), slot_rect)
                pygame.draw.rect(self.screen, (60, 40, 80), slot_rect, 1)
                self.backpack_slots.append((slot_rect, None))

    def _draw_dragged_item(self, mouse_x, mouse_y):
        """Draw the item being dragged at the mouse position."""
        if not self.dragging_item:
            return
        item = self.dragging_item
        size = 40
        x = mouse_x - size // 2
        y = mouse_y - size // 2

        # Semi-transparent background
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        item_color = self.get_item_color(item.name)
        s.fill((*item_color, 180))
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, size, size), 2)

        # Item letter
        letter = self.get_item_letter(item.name)
        text = self.fonts['medium'].render(letter, True, self.colors['text'])
        text_rect = text.get_rect(center=(mouse_x, mouse_y))
        self.screen.blit(text, text_rect)

        # Item name below
        name_text = self.fonts['tiny'].render(item.name, True, (255, 200, 100))
        name_rect = name_text.get_rect(center=(mouse_x, mouse_y + size // 2 + 10))
        self.screen.blit(name_text, name_rect)
                
    def _draw_dragged_shop_entry(self, mouse_x, mouse_y):
        """Draw the shop entry being dragged at the mouse position."""
        entry = self.dragging_shop_entry
        if not entry:
            return

        size = self.tile_size - 4

        if isinstance(entry, CharacterShopEntry):
            # Draw as a unit ghost
            x = mouse_x - size // 2
            y = mouse_y - size // 2
            unit_color = self.colors.get(entry.unit_type.name.lower(), (100, 200, 100))
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.screen.blit(s, (x, y))
            pygame.draw.rect(self.screen, self.colors['player_border'], (x, y, size, size), 3)
            letter = entry.unit_type.name[0].upper()
            text = self.fonts['large'].render(letter, True, unit_color)
            text_rect = text.get_rect(center=(mouse_x, mouse_y - 5))
            self.screen.blit(text, text_rect)
            # Name + cost
            label = self.fonts['tiny'].render(f"{entry.name} ({entry.cost}g)", True, (255, 200, 100))
            label_rect = label.get_rect(center=(mouse_x, mouse_y + size // 2 + 10))
            self.screen.blit(label, label_rect)

        elif isinstance(entry, ItemShopEntry):
            # Draw as an item icon
            item_size = 40
            x = mouse_x - item_size // 2
            y = mouse_y - item_size // 2
            s = pygame.Surface((item_size, item_size), pygame.SRCALPHA)
            s.fill((100, 150, 200, 180))
            self.screen.blit(s, (x, y))
            pygame.draw.rect(self.screen, (255, 255, 255), (x, y, item_size, item_size), 2)
            text = self.fonts['medium'].render("I", True, self.colors['text'])
            text_rect = text.get_rect(center=(mouse_x, mouse_y))
            self.screen.blit(text, text_rect)
            label = self.fonts['tiny'].render(f"{entry.name} ({entry.cost}g)", True, (255, 200, 100))
            label_rect = label.get_rect(center=(mouse_x, mouse_y + item_size // 2 + 10))
            self.screen.blit(label, label_rect)

    def draw_enemy_augments(self):
        """Draw enemy augments stacked vertically on the right side"""
        if not self.game.enemy_team.augments:
            return
            
        # Import augment types
        from augment import PassiveAugment, ItemAugment, UnitAugment
        
        # Panel dimensions (mirrored from player side)
        panel_width = 200
        panel_height = min(600, len(self.game.enemy_team.augments) * 60 + 40)
        panel_x = self.width - panel_width - 20  # Right side
        panel_y = 100  # Start below top UI panel
        
        # Draw background panel
        pygame.draw.rect(self.screen, self.colors['panel_bg'], 
                        (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, self.colors['enemy_border'],  # Use enemy border color
                        (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Title
        title_text = self.fonts['medium'].render("ENEMY AUGMENTS", True, self.colors['enemy_border'])
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        # Draw augments stacked vertically
        for i, augment in enumerate(self.game.enemy_team.augments):
            augment_y = panel_y + 40 + i * 55
            augment_rect = pygame.Rect(panel_x + 10, augment_y, panel_width - 20, 50)
            
            # Store rect for tooltip and click detection
            augment.ui_rect = augment_rect
            
            # Augment background
            bg_color = self.colors['button']
            pygame.draw.rect(self.screen, bg_color, augment_rect)
            pygame.draw.rect(self.screen, self.colors['panel_border'], augment_rect, 1)
            
            # Augment type indicator
            if isinstance(augment, PassiveAugment):
                aug_color = (150, 100, 200)  # Purple for passives
                aug_letter = 'P'
            elif isinstance(augment, ItemAugment):
                aug_color = (100, 150, 200)  # Blue for items
                aug_letter = 'I'
            elif isinstance(augment, UnitAugment):
                aug_color = (200, 150, 100)  # Gold for units
                aug_letter = 'U'
            else:
                aug_color = (150, 150, 150)  # Gray for unknown
                aug_letter = '?'
            
            # Draw type icon
            icon_size = 30
            icon_x = augment_rect.x + 5
            icon_y = augment_rect.y + 10
            pygame.draw.rect(self.screen, aug_color, (icon_x, icon_y, icon_size, icon_size))
            
            # Type letter
            letter_text = self.fonts['medium'].render(aug_letter, True, self.colors['text'])
            letter_rect = letter_text.get_rect(center=(icon_x + icon_size // 2, icon_y + icon_size // 2))
            self.screen.blit(letter_text, letter_rect)
            
            # Augment name (truncated if too long) - centered vertically in the box
            name = augment.name[:20] + '...' if len(augment.name) > 20 else augment.name
            name_text = self.fonts['small'].render(name, True, self.colors['text'])
            # Center the name vertically in the augment rect
            name_y = augment_rect.y + (augment_rect.height - name_text.get_height()) // 2
            self.screen.blit(name_text, (icon_x + icon_size + 10, name_y))
                
    def draw_shop(self):
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        if self.shop_open == ShopType.UNIT:
            self.draw_unit_shop()
            
    def draw_unit_shop(self):
        units = get_available_units()
        shop_width = 480
        shop_height = 480
        shop_x = self.width // 2 - shop_width // 2
        shop_y = self.height // 2 - shop_height // 2
        
        # Shop background (with optional red flash effect)
        bg_color = self.colors['panel_bg']
        border_color = self.colors['panel_border']
        if self.shop_flash_timer > 0:
            # Mix red flash color with normal colors
            flash_intensity = self.shop_flash_timer / self.shop_flash_duration
            bg_color = self._blend_colors(bg_color, self.colors['panel_flash_red'], flash_intensity * 0.4)
            border_color = self._blend_colors(border_color, self.colors['panel_flash_red'], flash_intensity * 0.6)
        
        pygame.draw.rect(self.screen, bg_color, (shop_x, shop_y, shop_width, shop_height))
        pygame.draw.rect(self.screen, border_color, (shop_x, shop_y, shop_width, shop_height), 3)
        
        # Title
        title = self.fonts['large'].render("CHOOSE A UNIT", True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, shop_y + 30))
        self.screen.blit(title, title_rect)
        
        # Units
        cols = 4
        for i, unit_type in enumerate(units):
            x = shop_x + 40 + (i % cols) * 110
            y = shop_y + 80 + (i // cols) * 120
            
            cost = self.game.get_unit_cost(unit_type)
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
        # Generate fresh tooltip content based on tooltip type
        tooltip_content = None
        
        if self.tooltip_type == "unit" and self.tooltip_unit:
            tooltip_content = self.create_unit_tooltip(self.tooltip_unit)
        elif self.tooltip_type == "shop_unit" and self.tooltip_unit:
            tooltip_content = self.create_shop_unit_tooltip(self.tooltip_unit)
        elif self.tooltip_type == "ability" and self.tooltip_skill:
            tooltip_content = self.create_ability_tooltip(self.tooltip_skill)
        elif self.tooltip_type == "augment" and self.tooltip_augment:
            tooltip_content = self.tooltip_augment.get_tooltip()
        elif self.tooltip_type == "item" and self.tooltip_item:
            tooltip_content = self.create_item_tooltip(self.tooltip_item)
        elif self.tooltip:
            # Fallback to old static tooltip system
            tooltip_content = self.tooltip
        
        if not tooltip_content:
            return
            
        raw_lines = tooltip_content.split('\n')
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
                # Handle both None and missing remaining_duration
                try:
                    if hasattr(status, 'remaining_duration') and status.remaining_duration is not None:
                        duration_text = f" ({status.remaining_duration:.1f}s)"
                    else:
                        duration_text = ""  # Permanent effect
                except (TypeError, AttributeError):
                    duration_text = ""  # Permanent effect
                lines.append(f"• {status.name}{duration_text}")
                
        return '\n'.join(lines)
    
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
        
        return '\n'.join(lines)
    
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
                    
        return '\n'.join(lines)
    
    def draw_combat_result_banner(self):
        """Draw victory or defeat banner during post-combat phase"""
        if not hasattr(self.game, 'combat_result') or not self.game.combat_result:
            return
            
        # Create banner text
        if self.game.combat_result == "victory":
            text = "VICTORY!"
            color = (100, 255, 100)  # Green
            bg_color = (0, 100, 0)
        else:
            text = "DEFEAT!"
            color = (255, 100, 100)  # Red
            bg_color = (100, 0, 0)
        
        # Create large font if not exists
        if not hasattr(self, 'banner_font'):
            self.banner_font = pygame.font.Font(None, 120)
            
        # Render text
        text_surface = self.banner_font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        
        # Draw background box with border
        padding = 40
        bg_rect = text_rect.inflate(padding * 2, padding)
        
        # Semi-transparent background
        s = pygame.Surface((bg_rect.width, bg_rect.height))
        s.set_alpha(200)
        s.fill(bg_color)
        self.screen.blit(s, bg_rect)
        
        # Border
        pygame.draw.rect(self.screen, color, bg_rect, 5)
        
        # Draw text
        self.screen.blit(text_surface, text_rect)
        
        # Show additional info
        if self.game.combat_result == "victory":
            sub_text = f"Wins: {self.game.player_wins}/20"
        else:
            sub_text = f"Lives: {self.game.player_lives}/5"
            
        sub_surface = self.fonts['large'].render(sub_text, True, color)
        sub_rect = sub_surface.get_rect(center=(self.width // 2, self.height // 2 + 80))
        self.screen.blit(sub_surface, sub_rect)


if __name__ == "__main__":
    ui = PyUI()
    ui.run()