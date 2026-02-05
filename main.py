"""
Hell Survivor - A Top-Down Survival Action Game
================================================
A hero is trapped on a platform in hell, surrounded by lava. They must fight
demons and defeat the boss to survive!

Features:
- SNES/GBA-style pixel art graphics with CRT filter
- Resizable window with fullscreen support (F11)
- Authentic retro game feel with dark hell theme

Controls:
- WASD or Arrow Keys: Move
- SPACE: Attack (requires sword)
- R: Restart (on game over)
- F11: Toggle fullscreen

Requirements: pygame-ce
"""

import pygame
import random
import math
import numpy as np
import asyncio
from enum import Enum
from typing import List, Optional, Tuple
from collections import deque

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# =============================================================================
# CONSTANTS
# =============================================================================

# Internal rendering resolution (low-res for retro feel, then upscaled)
INTERNAL_WIDTH = 640
INTERNAL_HEIGHT = 360

# Default window size (will be scaled up from internal)
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
FPS = 60

# Map size (in internal resolution scale)
MAP_WIDTH = 960
MAP_HEIGHT = 540

# =============================================================================
# RETRO COLOR PALETTE (SNES/GBA style limited palette) - HELL THEME
# =============================================================================
WHITE = (248, 248, 248)
BLACK = (16, 16, 16)
RED = (224, 64, 64)
GREEN = (64, 200, 64)
BLUE = (64, 112, 200)
YELLOW = (240, 216, 64)
GREY = (168, 168, 168)
BROWN = (152, 96, 56)
DARK_GREEN = (48, 128, 48)
LAVA_DARK = (160, 40, 20)  # Deep lava
LAVA = (220, 80, 30)  # Bright lava
LAVA_BRIGHT = (255, 140, 40)  # Lava highlights
ROCK_DARK = (50, 40, 45)  # Dark hellish rock
ROCK = (80, 65, 70)  # Main platform rock
ROCK_LIGHT = (100, 85, 90)  # Rock highlights
ORANGE = (232, 144, 56)
PINK = (240, 168, 176)
DARK_BROWN = (96, 64, 40)
LIGHT_BROWN = (200, 168, 128)
PURPLE = (144, 64, 176)
# Demon Hunter colors
HUNTER_HOOD = (30, 25, 35)  # Dark hood/cloak
HUNTER_CLOAK = (45, 35, 50)  # Cloak body
HUNTER_ARMOR = (60, 55, 70)  # Dark armor
HUNTER_TRIM = (120, 80, 40)  # Bronze/copper trim
HUNTER_GLOW = (200, 60, 60)  # Glowing red eyes
HUNTER_SKIN = (200, 180, 160)  # Pale skin
HUNTER_SCAR = (180, 100, 100)  # Battle scars
SKIN_TONE = HUNTER_SKIN
HAIR_COLOR = HUNTER_HOOD
SHIRT_COLOR = HUNTER_ARMOR
PANTS_COLOR = (40, 35, 45)  # Dark pants
# Ghost colors (was monkey)
GHOST_BODY = (180, 180, 200)  # Pale ghostly white-blue
GHOST_DARK = (120, 120, 150)  # Darker ghost shade
GHOST_GLOW = (200, 200, 255)  # Ghost glow
# Skeleton colors (was snake)
BONE_WHITE = (230, 225, 215)  # Bone color
BONE_DARK = (180, 170, 160)  # Darker bone
BONE_SOCKET = (40, 30, 30)  # Eye sockets
# Satan colors (boss)
SATAN_RED = (180, 40, 40)  # Satan body
SATAN_DARK = (120, 20, 20)  # Darker red
SATAN_HORN = (60, 50, 40)  # Dark horns
DEAD_TREE_DARK = (60, 45, 35)  # Charred tree trunks
DEAD_TREE = (90, 70, 55)  # Dead tree branches

# Legacy aliases
SNAKE_GREEN = BONE_WHITE
SNAKE_LIGHT = BONE_DARK
MONKEY_FUR = GHOST_BODY
MONKEY_FACE = GHOST_GLOW

# Legacy aliases for compatibility
SAND = ROCK
WATER = LAVA_DARK

# Player settings
PLAYER_WIDTH = 12
PLAYER_HEIGHT = 20
PLAYER_SPEED = 1.5
PLAYER_MAX_HEALTH = 100
PLAYER_ATTACK_RANGE = 32
PLAYER_ATTACK_WIDTH = 28
PLAYER_ATTACK_DURATION = 18  # frames (faster slash)

# Dodge roll settings
DODGE_DURATION = 12  # Frames of rolling
DODGE_SPEED = 5.0  # Speed during roll
DODGE_COOLDOWN = 45  # Frames before can dodge again

# Enemy settings
MONKEY_SIZE = 14
MONKEY_SPEED = 0.6
MONKEY_DAMAGE = 5
MONKEY_HEALTH = 1

SNAKE_SEGMENT_SIZE = 6
SNAKE_NUM_SEGMENTS = 8
SNAKE_SPEED = 0.8
SNAKE_DAMAGE = 10
SNAKE_HEALTH = 1

BOSS_SIZE = 32
BOSS_SPEED = 1.0
BOSS_DAMAGE = 30
BOSS_HEALTH = 7

# Item settings
SWORD_SIZE = (6, 14)
BOW_SIZE = (10, 12)
FOOD_SIZE = 8
LOOT_BAG_SIZE = 12

# Arrow settings
ARROW_SPEED = 6.0
ARROW_DAMAGE = 1  # Kills normal enemies in 1 hit
ARROW_LIFETIME = 120  # Frames before arrow disappears

# Bomb settings
BOMB_SIZE = (10, 10)
BOMB_SPEED = 4.0
BOMB_BASE_DAMAGE = 3
BOMB_BASE_RANGE = 40  # Explosion radius
BOMB_COOLDOWN = 90  # Frames between throws
BOMB_FLIGHT_TIME = 30  # Frames until explosion

# Spawn settings
ENEMY_SPAWN_INTERVAL = 3000
FOOD_SPAWN_INTERVAL = 5000
MAX_ENEMIES = 12
MAX_FOOD = 8

# Boss trigger settings
BOSS_TIME_TRIGGER = 60
BOSS_KILL_TRIGGER = 10

# Platform boundaries (lava is outside these bounds)
PLATFORM_MARGIN = 25  # Distance from map edge where lava begins
ISLAND_LEFT = PLATFORM_MARGIN
ISLAND_TOP = PLATFORM_MARGIN
ISLAND_RIGHT = MAP_WIDTH - PLATFORM_MARGIN
ISLAND_BOTTOM = MAP_HEIGHT - PLATFORM_MARGIN

# Tree configuration
TREE_COUNT = 12  # Number of trees to spawn
TREE_POSITIONS: List[Tuple[int, int]] = []  # Generated randomly each game

# Platform edge points (irregular rocky border)
PLATFORM_EDGE_POINTS: List[Tuple[int, int]] = []  # Generated each game
PLATFORM_INNER_POINTS: List[Tuple[int, int]] = []  # Inner platform surface

# Tree collision box (relative to tree position) - covers full tree including foliage
TREE_COLLISION_OFFSET_X = 0
TREE_COLLISION_OFFSET_Y = -6  # Foliage extends above tree position
TREE_COLLISION_WIDTH = 24
TREE_COLLISION_HEIGHT = 28  # From top of foliage to bottom of trunk

def generate_tree_positions() -> List[Tuple[int, int]]:
    """Generate random tree positions avoiding the center spawn area."""
    positions = []
    center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
    min_dist_from_center = 80  # Keep trees away from spawn area
    min_dist_between_trees = 60  # Minimum distance between trees
    
    attempts = 0
    while len(positions) < TREE_COUNT and attempts < 500:
        attempts += 1
        # Random position within island bounds (with margin for tree size)
        tx = random.randint(ISLAND_LEFT + 20, ISLAND_RIGHT - 40)
        ty = random.randint(ISLAND_TOP + 20, ISLAND_BOTTOM - 40)
        
        # Check distance from center
        dx = tx - center_x
        dy = ty - center_y
        if math.sqrt(dx*dx + dy*dy) < min_dist_from_center:
            continue
        
        # Check distance from other trees
        too_close = False
        for ox, oy in positions:
            dx = tx - ox
            dy = ty - oy
            if math.sqrt(dx*dx + dy*dy) < min_dist_between_trees:
                too_close = True
                break
        
        if not too_close:
            positions.append((tx, ty))
    
    return positions


def generate_platform_edge() -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Generate irregular rocky platform edge points."""
    outer_points = []
    inner_points = []
    
    # Platform dimensions
    left, top = ISLAND_LEFT, ISLAND_TOP
    right, bottom = ISLAND_RIGHT, ISLAND_BOTTOM
    width = right - left
    height = bottom - top
    
    # Number of points per side (more = more detail)
    points_per_side = 12
    
    # Maximum irregularity (pixels of deviation)
    max_jag = 8
    inner_offset = 6  # How far inner surface is from outer edge
    
    # Generate points going clockwise around the platform
    # Top edge (left to right)
    for i in range(points_per_side):
        t = i / points_per_side
        x = left + t * width
        jag = random.uniform(-max_jag, max_jag * 0.5)  # Mostly inward jags
        outer_points.append((x + random.uniform(-3, 3), top + jag))
        inner_points.append((x + random.uniform(-2, 2), top + inner_offset + abs(jag) * 0.5))
    
    # Right edge (top to bottom)
    for i in range(points_per_side):
        t = i / points_per_side
        y = top + t * height
        jag = random.uniform(-max_jag * 0.5, max_jag)
        outer_points.append((right + jag, y + random.uniform(-3, 3)))
        inner_points.append((right - inner_offset - abs(jag) * 0.5, y + random.uniform(-2, 2)))
    
    # Bottom edge (right to left)
    for i in range(points_per_side):
        t = i / points_per_side
        x = right - t * width
        jag = random.uniform(-max_jag * 0.5, max_jag)
        outer_points.append((x + random.uniform(-3, 3), bottom + jag))
        inner_points.append((x + random.uniform(-2, 2), bottom - inner_offset - abs(jag) * 0.5))
    
    # Left edge (bottom to top)
    for i in range(points_per_side):
        t = i / points_per_side
        y = bottom - t * height
        jag = random.uniform(-max_jag, max_jag * 0.5)
        outer_points.append((left + jag, y + random.uniform(-3, 3)))
        inner_points.append((left + inner_offset + abs(jag) * 0.5, y + random.uniform(-2, 2)))
    
    return outer_points, inner_points


def get_tree_rects() -> List[pygame.Rect]:
    """Get collision rectangles for all trees."""
    rects = []
    for tx, ty in TREE_POSITIONS:
        rect = pygame.Rect(
            tx + TREE_COLLISION_OFFSET_X,
            ty + TREE_COLLISION_OFFSET_Y,
            TREE_COLLISION_WIDTH,
            TREE_COLLISION_HEIGHT
        )
        rects.append(rect)
    return rects

TREE_RECTS: List[pygame.Rect] = []  # Initialized in GameManager

def check_tree_collision(rect: pygame.Rect) -> bool:
    """Check if a rect collides with any tree."""
    for tree_rect in TREE_RECTS:
        if rect.colliderect(tree_rect):
            return True
    return False

def get_blocking_tree_index(rect: pygame.Rect) -> int:
    """Get the index of the tree blocking this rect, or -1 if none."""
    for i, tree_rect in enumerate(TREE_RECTS):
        if rect.colliderect(tree_rect):
            return i
    return -1

def destroy_tree(index: int) -> Tuple[int, int]:
    """Remove a tree by index. Returns the tree position or (-1, -1) if invalid."""
    global TREE_POSITIONS, TREE_RECTS
    if 0 <= index < len(TREE_POSITIONS):
        pos = TREE_POSITIONS.pop(index)
        TREE_RECTS.pop(index)
        return pos
    return (-1, -1)


# =============================================================================
# ENUMS
# =============================================================================

class Direction(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class EnemyType(Enum):
    MONKEY = 0  # Ghost (legacy name for compatibility)
    SNAKE = 1   # Skeleton (legacy name for compatibility)
    BOSS = 2    # Satan


class ItemType(Enum):
    SWORD = 0
    APPLE = 1
    BANANA = 2
    DURIAN = 3
    LOOT_BAG = 4
    BOW = 5
    BOMB = 6


class UpgradeType(Enum):
    SPEED_BOOST = 0
    VITALITY = 1
    IRON_SWORD = 2
    MULTI_ARROW = 3  # Extra arrow for bow
    MEGA_BOMB = 4  # Bigger explosion for bomb


# =============================================================================
# SOUND MANAGER CLASS - Retro-style procedural sounds
# =============================================================================

class SoundManager:
    """
    Generates and manages retro-style 8-bit sound effects.
    Uses procedural generation to create authentic chiptune sounds.
    """
    
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self._generate_sounds()
    
    def _generate_wave(self, frequency: float, duration: float, 
                       wave_type: str = 'square', volume: float = 0.3) -> pygame.mixer.Sound:
        """Generate a sound wave."""
        sample_rate = 22050
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        
        if wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == 'saw':
            wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        elif wave_type == 'triangle':
            wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        elif wave_type == 'sine':
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'noise':
            wave = np.random.uniform(-1, 1, n_samples).astype(np.float32)
        else:
            wave = np.sin(2 * np.pi * frequency * t)
        
        # Apply envelope (attack/decay)
        envelope = np.ones(n_samples, dtype=np.float32)
        attack = int(0.01 * sample_rate)
        decay = int(0.1 * sample_rate)
        if attack > 0:
            envelope[:attack] = np.linspace(0, 1, attack)
        if decay > 0 and decay < n_samples:
            envelope[-decay:] = np.linspace(1, 0, decay)
        
        wave = (wave * envelope * volume * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _generate_sounds(self) -> None:
        """Generate all game sound effects."""
        # Sword swing - quick sweep
        self.sounds['attack'] = self._create_attack_sound()
        
        # Enemy hit
        self.sounds['hit'] = self._generate_wave(200, 0.1, 'square', 0.25)
        
        # Enemy death
        self.sounds['enemy_death'] = self._create_death_sound()
        
        # Player hurt
        self.sounds['hurt'] = self._create_hurt_sound()
        
        # Pickup item
        self.sounds['pickup'] = self._create_pickup_sound()
        
        # Pickup sword
        self.sounds['sword_pickup'] = self._create_sword_pickup_sound()
        
        # Upgrade/loot
        self.sounds['upgrade'] = self._create_upgrade_sound()
        
        # Boss spawn
        self.sounds['boss_spawn'] = self._create_boss_spawn_sound()
        
        # Wave complete
        self.sounds['wave_complete'] = self._create_wave_complete_sound()
        
        # Game over
        self.sounds['game_over'] = self._create_game_over_sound()
        
        # Dodge roll
        self.sounds['dodge'] = self._create_dodge_sound()
    
    def _create_dodge_sound(self) -> pygame.mixer.Sound:
        """Create dodge roll whoosh sound."""
        sample_rate = 22050
        duration = 0.15
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        
        # Noise with envelope for whoosh effect
        noise = np.random.uniform(-1, 1, n_samples).astype(np.float32)
        # Bandpass-like effect using modulation
        freq_mod = 300 + 200 * t / duration
        carrier = np.sin(2 * np.pi * freq_mod * t)
        wave = noise * 0.3 + carrier * 0.2
        
        envelope = np.sin(np.pi * t / duration) * 0.4
        wave = (wave * envelope * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_attack_sound(self) -> pygame.mixer.Sound:
        """Create sword swing sound."""
        sample_rate = 22050
        duration = 0.12
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        
        # Frequency sweep from high to low
        freq = 800 - 600 * t / duration
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * 0.2
        
        envelope = np.linspace(1, 0, n_samples)
        wave = (wave * envelope * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_death_sound(self) -> pygame.mixer.Sound:
        """Create enemy death sound."""
        sample_rate = 22050
        duration = 0.2
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        
        freq = 400 - 300 * t / duration
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * 0.25
        envelope = np.linspace(1, 0, n_samples)
        wave = (wave * envelope * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_hurt_sound(self) -> pygame.mixer.Sound:
        """Create player hurt sound."""
        sample_rate = 22050
        duration = 0.15
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        
        freq = 150 + 50 * np.sin(60 * np.pi * t)
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * 0.3
        envelope = np.linspace(1, 0, n_samples)
        wave = (wave * envelope * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_pickup_sound(self) -> pygame.mixer.Sound:
        """Create item pickup sound."""
        sample_rate = 22050
        duration = 0.1
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        
        freq = 600 + 400 * t / duration
        wave = np.sin(2 * np.pi * freq * t) * 0.25
        envelope = 1 - t / duration
        wave = (wave * envelope * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_sword_pickup_sound(self) -> pygame.mixer.Sound:
        """Create sword pickup fanfare."""
        sample_rate = 22050
        notes = [(523, 0.1), (659, 0.1), (784, 0.15)]  # C5, E5, G5
        waves = []
        
        for freq, dur in notes:
            n = int(dur * sample_rate)
            t = np.linspace(0, dur, n, dtype=np.float32)
            w = np.sign(np.sin(2 * np.pi * freq * t)) * 0.25
            env = np.linspace(1, 0.3, n)
            waves.append((w * env * 32767).astype(np.int16))
        
        wave = np.concatenate(waves)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_upgrade_sound(self) -> pygame.mixer.Sound:
        """Create upgrade/power-up sound."""
        sample_rate = 22050
        notes = [(392, 0.08), (523, 0.08), (659, 0.08), (784, 0.15)]  # G4, C5, E5, G5
        waves = []
        
        for freq, dur in notes:
            n = int(dur * sample_rate)
            t = np.linspace(0, dur, n, dtype=np.float32)
            w = (np.sign(np.sin(2 * np.pi * freq * t)) * 0.5 + 
                 np.sin(2 * np.pi * freq * t) * 0.5) * 0.25
            env = np.linspace(1, 0.5, n)
            waves.append((w * env * 32767).astype(np.int16))
        
        wave = np.concatenate(waves)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_boss_spawn_sound(self) -> pygame.mixer.Sound:
        """Create ominous boss spawn sound."""
        sample_rate = 22050
        duration = 0.5
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, dtype=np.float32)
        
        freq = 80 + 20 * np.sin(8 * np.pi * t)
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * 0.35
        envelope = np.sin(np.pi * t / duration)
        wave = (wave * envelope * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_wave_complete_sound(self) -> pygame.mixer.Sound:
        """Create victory fanfare."""
        sample_rate = 22050
        notes = [(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.25)]  # C5, E5, G5, C6
        waves = []
        
        for freq, dur in notes:
            n = int(dur * sample_rate)
            t = np.linspace(0, dur, n, dtype=np.float32)
            w = np.sign(np.sin(2 * np.pi * freq * t)) * 0.3
            env = np.linspace(1, 0.4, n)
            waves.append((w * env * 32767).astype(np.int16))
        
        wave = np.concatenate(waves)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def _create_game_over_sound(self) -> pygame.mixer.Sound:
        """Create sad game over sound."""
        sample_rate = 22050
        notes = [(392, 0.2), (330, 0.2), (262, 0.4)]  # G4, E4, C4 descending
        waves = []
        
        for freq, dur in notes:
            n = int(dur * sample_rate)
            t = np.linspace(0, dur, n, dtype=np.float32)
            w = np.sign(np.sin(2 * np.pi * freq * t)) * 0.3
            env = np.linspace(1, 0.3, n)
            waves.append((w * env * 32767).astype(np.int16))
        
        wave = np.concatenate(waves)
        stereo_wave = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo_wave)
    
    def play(self, sound_name: str) -> None:
        """Play a sound by name."""
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()
# =============================================================================

class CRTFilter:
    """
    Applies retro CRT-style visual effects:
    - Scanlines
    - Slight color bleeding
    - Vignette effect
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.scanline_surface = self._create_scanlines()
        self.vignette_surface = self._create_vignette()
    
    def _create_scanlines(self) -> pygame.Surface:
        """Create scanline overlay."""
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 2):
            pygame.draw.line(surface, (0, 0, 0, 40), (0, y), (self.width, y))
        return surface
    
    def _create_vignette(self) -> pygame.Surface:
        """Create vignette (darkened corners) effect."""
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width // 2, self.height // 2
        max_dist = math.sqrt(cx * cx + cy * cy)
        
        for y in range(0, self.height, 4):
            for x in range(0, self.width, 4):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                alpha = int((dist / max_dist) ** 2 * 60)
                pygame.draw.rect(surface, (0, 0, 0, alpha), (x, y, 4, 4))
        
        return surface
    
    def resize(self, width: int, height: int) -> None:
        """Recreate filters for new size."""
        self.width = width
        self.height = height
        self.scanline_surface = self._create_scanlines()
        self.vignette_surface = self._create_vignette()
    
    def apply(self, screen: pygame.Surface) -> None:
        """Apply CRT effects to the screen."""
        screen.blit(self.scanline_surface, (0, 0))
        screen.blit(self.vignette_surface, (0, 0))


# =============================================================================
# CAMERA CLASS
# =============================================================================

class Camera:
    """Camera that follows the player."""
    
    def __init__(self, width: int, height: int, map_width: int, map_height: int):
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height
        self.x = 0
        self.y = 0
        # Screen shake
        self.shake_intensity = 0
        self.shake_duration = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0
    
    def shake(self, intensity: int = 5, duration: int = 10) -> None:
        """Trigger camera shake effect."""
        self.shake_intensity = intensity
        self.shake_duration = duration
    
    def update(self, target_x: float, target_y: float) -> None:
        """Update camera position to center on target."""
        self.x = target_x - self.width // 2
        self.y = target_y - self.height // 2
        self.x = max(0, min(self.x, self.map_width - self.width))
        self.y = max(0, min(self.y, self.map_height - self.height))
        
        # Update shake
        if self.shake_duration > 0:
            self.shake_offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_duration -= 1
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0
    
    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Convert world coordinates to screen coordinates."""
        return pygame.Rect(
            rect.x - self.x + self.shake_offset_x, 
            rect.y - self.y + self.shake_offset_y, 
            rect.width, rect.height
        )
    
    def apply_pos(self, x: float, y: float) -> Tuple[float, float]:
        """Convert world position to screen position."""
        return (x - self.x + self.shake_offset_x, y - self.y + self.shake_offset_y)
    
    def get_spawn_zone(self) -> Tuple[int, int, int, int]:
        """Get the area just outside the camera view."""
        margin = 30
        return (
            int(self.x - margin),
            int(self.y - margin),
            int(self.x + self.width + margin),
            int(self.y + self.height + margin)
        )


# =============================================================================
# PLAYER CLASS - GBA-STYLE HUMAN CHARACTER
# =============================================================================

class Player:
    """
    GBA-style human character with walk cycle animation and attack animation.
    """
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.speed = PLAYER_SPEED
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.has_sword = False
        self.direction = Direction.DOWN
        
        # Animation state
        self.walk_frame = 0
        self.walk_timer = 0
        self.is_moving = False
        
        # Attack state
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_range = PLAYER_ATTACK_RANGE
        self.attack_width = PLAYER_ATTACK_WIDTH
        
        # Upgrades
        self.speed_multiplier = 1.0
        self.sword_level = 0  # Each level: +1 damage, +20% range
        self.extra_arrows = 0  # Number of extra arrows from upgrades
        
        # Weapon type
        self.has_sword = False
        self.has_bow = False
        self.has_bomb = False
        
        # Bow attack state
        self.bow_cooldown = 0
        self.bow_cooldown_max = 30  # Frames between shots
        
        # Bomb state
        self.bomb_cooldown = 0
        self.bomb_level = 0  # Each level: +1 damage, +10 range
        
        # Dodge roll state
        self.is_dodging = False
        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.dodge_direction = (0, 1)  # Direction of dodge
        
        # EXP and Level system
        self.exp = 0
        self.level = 1
        self.exp_per_level = 100
        
        # Invincibility frames after taking damage
        self.invincible_timer = 0
    
    def gain_exp(self, amount: int) -> bool:
        """Add EXP and check for level up. Returns True if leveled up."""
        self.exp += amount
        leveled_up = False
        while self.exp >= self.exp_per_level:
            self.exp -= self.exp_per_level
            self.level += 1
            # +3% speed per level
            self.speed_multiplier += 0.03
            # +5 max HP per level (and heal the bonus)
            self.max_health += 5
            self.health += 5
            leveled_up = True
        return leveled_up
    
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def handle_input(self, keys) -> None:
        """Process movement input."""
        old_x, old_y = self.x, self.y
        
        # During dodge, move in dodge direction
        if self.is_dodging:
            dx, dy = self.dodge_direction
            self.x += dx * DODGE_SPEED
            self.y += dy * DODGE_SPEED
            self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
            self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
            # Check tree collision
            if check_tree_collision(self.rect):
                self.x, self.y = old_x, old_y
            return
        
        dx, dy = 0, 0
        self.is_moving = False
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
            self.direction = Direction.UP
            self.is_moving = True
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
            self.direction = Direction.DOWN
            self.is_moving = True
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
            self.direction = Direction.LEFT
            self.is_moving = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
            self.direction = Direction.RIGHT
            self.is_moving = True
        
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        
        actual_speed = self.speed * self.speed_multiplier
        self.x += dx * actual_speed
        self.y += dy * actual_speed
        self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
        self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
        
        # Check tree collision - try to slide along axes
        if check_tree_collision(self.rect):
            # Try moving only on x axis
            self.y = old_y
            if check_tree_collision(self.rect):
                # Try moving only on y axis
                self.x = old_x
                self.y = old_y + dy * actual_speed
                self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
                if check_tree_collision(self.rect):
                    # Can't move at all
                    self.x, self.y = old_x, old_y
    
    def attack(self) -> bool:
        """Initiate attack."""
        if self.has_sword and not self.is_attacking and not self.is_dodging:
            self.is_attacking = True
            self.attack_timer = PLAYER_ATTACK_DURATION
            return True
        return False
    
    def dodge(self) -> bool:
        """Initiate dodge roll."""
        if self.dodge_cooldown <= 0 and not self.is_dodging and not self.is_attacking:
            self.is_dodging = True
            self.dodge_timer = DODGE_DURATION
            self.dodge_cooldown = DODGE_COOLDOWN
            
            # Set dodge direction based on current facing
            if self.direction == Direction.UP:
                self.dodge_direction = (0, -1)
            elif self.direction == Direction.DOWN:
                self.dodge_direction = (0, 1)
            elif self.direction == Direction.LEFT:
                self.dodge_direction = (-1, 0)
            else:
                self.dodge_direction = (1, 0)
            return True
        return False
    
    def get_attack_rect(self) -> Optional[pygame.Rect]:
        """Get attack hitbox."""
        if not self.is_attacking:
            return None
        
        cx, cy = self.center
        # Each sword level adds 25% range (compounds better)
        range_multiplier = 1.0 + self.sword_level * 0.25
        attack_range = self.attack_range * range_multiplier
        attack_width = self.attack_width * range_multiplier
        
        if self.direction == Direction.UP:
            return pygame.Rect(cx - attack_width // 2, cy - attack_range, attack_width, attack_range)
        elif self.direction == Direction.DOWN:
            return pygame.Rect(cx - attack_width // 2, cy, attack_width, attack_range)
        elif self.direction == Direction.LEFT:
            return pygame.Rect(cx - attack_range, cy - attack_width // 2, attack_range, attack_width)
        else:
            return pygame.Rect(cx, cy - attack_width // 2, attack_range, attack_width)
    
    def update(self) -> None:
        """Update animation states."""
        # Walk animation
        if self.is_moving and not self.is_dodging:
            self.walk_timer += 1
            if self.walk_timer >= 8:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 4
        else:
            self.walk_frame = 0
            self.walk_timer = 0
        
        # Attack animation
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False
        
        # Dodge roll
        if self.is_dodging:
            self.dodge_timer -= 1
            if self.dodge_timer <= 0:
                self.is_dodging = False
        
        # Dodge cooldown
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        
        # Bow cooldown
        if self.bow_cooldown > 0:
            self.bow_cooldown -= 1
        
        # Bomb cooldown
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1
        
        # Invincibility cooldown
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
    
    def take_damage(self, amount: int) -> None:
        # Can't take damage while invincible or dodging
        if self.invincible_timer > 0 or self.is_dodging:
            return
        self.health = max(0, self.health - amount)
        self.invincible_timer = 30  # 0.5 seconds of invincibility
    
    @property
    def sword_damage(self) -> int:
        """Get sword damage based on level. Base 2, scales exponentially."""
        # Level 0: 2, Level 1: 3, Level 2: 4, Level 3: 5, Level 4: 7, Level 5: 9, Level 6: 11...
        return 2 + self.sword_level + (self.sword_level // 2)
    
    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)
    
    def apply_upgrade(self, upgrade: UpgradeType) -> str:
        if upgrade == UpgradeType.SPEED_BOOST:
            self.speed_multiplier += 0.15
            return "Speed Boost!"
        elif upgrade == UpgradeType.VITALITY:
            self.max_health = 150
            self.health = self.max_health
            return "Vitality Up!"
        elif upgrade == UpgradeType.IRON_SWORD:
            self.sword_level += 1
            return f"Sword +{self.sword_level}!"
        elif upgrade == UpgradeType.MULTI_ARROW:
            self.extra_arrows += 1
            return f"Multi-Arrow! (+{self.extra_arrows})"
        else:  # MEGA_BOMB
            self.bomb_level += 1
            return f"Mega Bomb +{self.bomb_level}!"
    
    @property
    def bomb_damage(self) -> int:
        """Get bomb damage based on level."""
        return BOMB_BASE_DAMAGE + self.bomb_level * 2
    
    @property
    def bomb_range(self) -> int:
        """Get bomb explosion range based on level."""
        return BOMB_BASE_RANGE + self.bomb_level * 15
    
    def can_throw_bomb(self) -> bool:
        """Check if player can throw bomb."""
        return self.has_bomb and self.bomb_cooldown <= 0 and not self.is_attacking and not self.is_dodging
    
    def throw_bomb(self) -> bool:
        """Initiate bomb throw."""
        if self.can_throw_bomb():
            self.bomb_cooldown = BOMB_COOLDOWN
            return True
        return False
    
    def can_shoot(self) -> bool:
        """Check if player can shoot bow."""
        return self.has_bow and self.bow_cooldown <= 0 and not self.is_attacking and not self.is_dodging
    
    def shoot(self) -> bool:
        """Initiate bow shot."""
        if self.can_shoot():
            self.bow_cooldown = self.bow_cooldown_max
            return True
        return False
    
    def get_arrow_directions(self) -> List[Tuple[float, float]]:
        """Get directions for all arrows to shoot."""
        # Base direction based on facing
        if self.direction == Direction.UP:
            base = (0, -1)
        elif self.direction == Direction.DOWN:
            base = (0, 1)
        elif self.direction == Direction.LEFT:
            base = (-1, 0)
        else:
            base = (1, 0)
        
        directions = [base]
        
        # Add spread arrows based on upgrades - each upgrade adds 2 more arrows
        # Use constant small angle increment so arrows always spread evenly
        for i in range(self.extra_arrows):
            # Fixed 6 degree (~0.1 radian) increment per arrow pair
            angle = 0.1 * (i + 1)
            if base[0] != 0:  # Horizontal
                directions.append((base[0], angle))
                directions.append((base[0], -angle))
            else:  # Vertical
                directions.append((angle, base[1]))
                directions.append((-angle, base[1]))
        
        # Normalize directions
        normalized = []
        for dx, dy in directions:
            length = math.sqrt(dx*dx + dy*dy)
            normalized.append((dx/length, dy/length))
        
        return normalized
    
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw GBA-style human sprite."""
        sx, sy = camera.apply_pos(self.x, self.y)
        sx, sy = int(sx), int(sy)
        
        # Skip drawing every other frame when invincible (flashing effect)
        if self.invincible_timer > 0 and (self.invincible_timer // 3) % 2 == 0:
            return
        
        # Dodge roll animation - draw spinning ball with afterimages
        if self.is_dodging:
            self._draw_dodge_roll(screen, sx, sy, camera)
            return
        
        # Calculate leg offset for walk animation
        leg_offsets = [0, 1, 0, -1]  # Walking bob
        leg_offset = leg_offsets[self.walk_frame] if self.is_moving else 0
        
        # Attack swing angle
        swing_angle = 0
        if self.is_attacking:
            progress = 1 - (self.attack_timer / PLAYER_ATTACK_DURATION)
            swing_angle = math.sin(progress * math.pi) * 60
        
        # Draw based on direction
        if self.direction == Direction.DOWN:
            self._draw_front(screen, sx, sy, leg_offset, swing_angle)
        elif self.direction == Direction.UP:
            self._draw_back(screen, sx, sy, leg_offset, swing_angle)
        elif self.direction == Direction.LEFT:
            self._draw_side(screen, sx, sy, leg_offset, swing_angle, flip=True)
        else:
            self._draw_side(screen, sx, sy, leg_offset, swing_angle, flip=False)
    
    def _draw_front(self, screen: pygame.Surface, sx: int, sy: int, leg_offset: int, swing: float) -> None:
        """Draw demon hunter facing down (front view)."""
        # Hood/cloak top
        pygame.draw.polygon(screen, HUNTER_HOOD, [
            (sx + 1, sy + 8), (sx + 6, sy - 1), (sx + 11, sy + 8)
        ])  # Hood peak
        pygame.draw.rect(screen, HUNTER_HOOD, (sx + 1, sy + 2, 10, 6))  # Hood sides
        
        # Face (shadowed under hood)
        pygame.draw.rect(screen, HUNTER_SKIN, (sx + 3, sy + 4, 6, 5))  # Face
        
        # Glowing red eyes
        pygame.draw.rect(screen, HUNTER_GLOW, (sx + 4, sy + 5, 2, 2))
        pygame.draw.rect(screen, HUNTER_GLOW, (sx + 7, sy + 5, 2, 2))
        # Eye glow effect
        pygame.draw.rect(screen, (255, 100, 100), (sx + 4, sy + 5, 1, 1))
        pygame.draw.rect(screen, (255, 100, 100), (sx + 8, sy + 5, 1, 1))
        
        # Scar across face
        pygame.draw.line(screen, HUNTER_SCAR, (sx + 3, sy + 6), (sx + 5, sy + 8), 1)
        
        # Body - armored torso with cloak
        pygame.draw.rect(screen, HUNTER_ARMOR, (sx + 2, sy + 9, 8, 6))  # Armor
        pygame.draw.rect(screen, HUNTER_TRIM, (sx + 5, sy + 9, 2, 6))  # Center trim
        # Shoulder pauldrons
        pygame.draw.rect(screen, HUNTER_TRIM, (sx + 1, sy + 9, 3, 2))
        pygame.draw.rect(screen, HUNTER_TRIM, (sx + 8, sy + 9, 3, 2))
        
        # Cloak sides
        pygame.draw.polygon(screen, HUNTER_CLOAK, [
            (sx, sy + 8), (sx - 1, sy + 18), (sx + 2, sy + 15)
        ])
        pygame.draw.polygon(screen, HUNTER_CLOAK, [
            (sx + 12, sy + 8), (sx + 13, sy + 18), (sx + 10, sy + 15)
        ])
        
        # Arms with gauntlets
        arm_y = sy + 9
        if self.is_attacking and self.has_sword:
            # Slashing animation - demon slayer sword
            progress = 1 - (self.attack_timer / PLAYER_ATTACK_DURATION)
            slash_angle = -60 + progress * 120
            sword_len = 24 + self.sword_level * 3
            
            cx, cy = sx + 6, sy + 12
            angle_rad = math.radians(slash_angle)
            tip_x = cx + math.sin(angle_rad) * sword_len
            tip_y = cy + math.cos(angle_rad) * sword_len
            
            # Demon slayer blade (dark with red edge)
            pygame.draw.line(screen, (80, 80, 90), (cx, cy), (int(tip_x), int(tip_y)), 4)
            pygame.draw.line(screen, HUNTER_GLOW, (cx, cy), (int(tip_x), int(tip_y)), 2)
            pygame.draw.circle(screen, HUNTER_TRIM, (cx, cy), 3)  # Ornate hilt
            
            pygame.draw.rect(screen, HUNTER_TRIM, (sx + 8, arm_y, 4, 4))  # Gauntlet
        else:
            pygame.draw.rect(screen, HUNTER_TRIM, (sx, arm_y, 2, 5))  # Left gauntlet
            pygame.draw.rect(screen, HUNTER_TRIM, (sx + 10, arm_y, 2, 5))  # Right gauntlet
        
        # Legs with armored boots
        leg_spread = abs(leg_offset)
        pygame.draw.rect(screen, PANTS_COLOR, (sx + 3 - leg_spread, sy + 15, 3, 4))
        pygame.draw.rect(screen, PANTS_COLOR, (sx + 7 + leg_spread, sy + 15, 3, 4))
        # Boots
        pygame.draw.rect(screen, HUNTER_HOOD, (sx + 3 - leg_spread, sy + 18, 3, 2))
        pygame.draw.rect(screen, HUNTER_HOOD, (sx + 7 + leg_spread, sy + 18, 3, 2))
    
    def _draw_back(self, screen: pygame.Surface, sx: int, sy: int, leg_offset: int, swing: float) -> None:
        """Draw demon hunter facing up (back view)."""
        # Hood from behind
        pygame.draw.polygon(screen, HUNTER_HOOD, [
            (sx + 1, sy + 8), (sx + 6, sy - 1), (sx + 11, sy + 8)
        ])
        pygame.draw.rect(screen, HUNTER_HOOD, (sx + 1, sy + 2, 10, 7))
        
        # Cloak/cape flowing behind
        pygame.draw.polygon(screen, HUNTER_CLOAK, [
            (sx, sy + 8), (sx - 2, sy + 20), (sx + 6, sy + 18),
            (sx + 14, sy + 20), (sx + 12, sy + 8)
        ])
        # Cloak inner shadow
        pygame.draw.polygon(screen, HUNTER_HOOD, [
            (sx + 2, sy + 10), (sx + 1, sy + 17), (sx + 6, sy + 16),
            (sx + 11, sy + 17), (sx + 10, sy + 10)
        ])
        
        # Demon hunter symbol on back (red glyph)
        pygame.draw.line(screen, HUNTER_GLOW, (sx + 4, sy + 11), (sx + 8, sy + 11), 1)
        pygame.draw.line(screen, HUNTER_GLOW, (sx + 6, sy + 10), (sx + 6, sy + 14), 1)
        
        # Armored body (visible through cloak opening)
        pygame.draw.rect(screen, HUNTER_ARMOR, (sx + 3, sy + 8, 6, 6))
        pygame.draw.rect(screen, HUNTER_TRIM, (sx + 5, sy + 8, 2, 6))
        
        # Arms
        arm_y = sy + 8
        if self.is_attacking and self.has_sword:
            progress = 1 - (self.attack_timer / PLAYER_ATTACK_DURATION)
            slash_angle = 60 - progress * 120
            sword_len = 24 + self.sword_level * 3
            
            cx, cy = sx + 6, sy + 10
            angle_rad = math.radians(slash_angle)
            tip_x = cx + math.sin(angle_rad) * sword_len
            tip_y = cy - math.cos(angle_rad) * sword_len
            
            pygame.draw.line(screen, (80, 80, 90), (cx, cy), (int(tip_x), int(tip_y)), 4)
            pygame.draw.line(screen, HUNTER_GLOW, (cx, cy), (int(tip_x), int(tip_y)), 2)
            pygame.draw.circle(screen, HUNTER_TRIM, (cx, cy), 3)
            
            pygame.draw.rect(screen, HUNTER_TRIM, (sx + 8, arm_y, 4, 4))
        else:
            pygame.draw.rect(screen, HUNTER_TRIM, (sx, arm_y, 2, 5))
            pygame.draw.rect(screen, HUNTER_TRIM, (sx + 10, arm_y, 2, 5))
        
        # Legs and boots
        leg_spread = abs(leg_offset)
        pygame.draw.rect(screen, PANTS_COLOR, (sx + 3 - leg_spread, sy + 15, 3, 4))
        pygame.draw.rect(screen, PANTS_COLOR, (sx + 7 + leg_spread, sy + 15, 3, 4))
        pygame.draw.rect(screen, HUNTER_HOOD, (sx + 3 - leg_spread, sy + 18, 3, 2))
        pygame.draw.rect(screen, HUNTER_HOOD, (sx + 7 + leg_spread, sy + 18, 3, 2))
    
    def _draw_side(self, screen: pygame.Surface, sx: int, sy: int, leg_offset: int, swing: float, flip: bool) -> None:
        """Draw demon hunter facing left or right (side view)."""
        # Cloak flowing behind
        cloak_x = sx + 10 if flip else sx - 2
        pygame.draw.polygon(screen, HUNTER_CLOAK, [
            (cloak_x, sy + 6), (cloak_x + (3 if flip else -3), sy + 18), 
            (cloak_x + (1 if flip else -1), sy + 10)
        ])
        
        # Hood (side profile)
        pygame.draw.polygon(screen, HUNTER_HOOD, [
            (sx + 2, sy + 7), (sx + 6, sy - 1), (sx + 10, sy + 7)
        ])
        pygame.draw.rect(screen, HUNTER_HOOD, (sx + 2, sy + 2, 8, 6))
        
        # Face visible from side (shadowed)
        face_x = sx + 2 if flip else sx + 5
        pygame.draw.rect(screen, HUNTER_SKIN, (face_x, sy + 4, 4, 4))
        
        # Glowing eye (one visible from side)
        eye_x = sx + 3 if flip else sx + 7
        pygame.draw.rect(screen, HUNTER_GLOW, (eye_x, sy + 5, 2, 2))
        pygame.draw.rect(screen, (255, 100, 100), (eye_x, sy + 5, 1, 1))
        
        # Armored body
        pygame.draw.rect(screen, HUNTER_ARMOR, (sx + 3, sy + 8, 6, 7))
        pygame.draw.rect(screen, HUNTER_TRIM, (sx + 4, sy + 8, 1, 7))  # Side trim
        pygame.draw.rect(screen, HUNTER_TRIM, (sx + 3, sy + 8, 6, 2))  # Shoulder
        
        # Arm with gauntlet
        arm_x = sx + 1 if flip else sx + 8
        if self.is_attacking and self.has_sword:
            progress = 1 - (self.attack_timer / PLAYER_ATTACK_DURATION)
            slash_angle = -45 + progress * 90
            sword_len = 24 + self.sword_level * 3
            
            if flip:
                cx, cy = sx + 2, sy + 11
                angle_rad = math.radians(180 + slash_angle)
            else:
                cx, cy = sx + 10, sy + 11
                angle_rad = math.radians(slash_angle)
            
            tip_x = cx + math.cos(angle_rad) * sword_len
            tip_y = cy + math.sin(angle_rad) * sword_len
            
            # Demon slayer blade
            pygame.draw.line(screen, (80, 80, 90), (cx, cy), (int(tip_x), int(tip_y)), 4)
            pygame.draw.line(screen, HUNTER_GLOW, (cx, cy), (int(tip_x), int(tip_y)), 2)
            pygame.draw.circle(screen, HUNTER_TRIM, (cx, cy), 3)
            
            pygame.draw.rect(screen, HUNTER_TRIM, (arm_x, sy + 9, 3, 4))
        else:
            pygame.draw.rect(screen, HUNTER_TRIM, (arm_x, sy + 9, 3, 5))
        
        # Legs with boots (alternating for walk)
        if self.is_moving:
            pygame.draw.rect(screen, PANTS_COLOR, (sx + 4 + leg_offset, sy + 15, 3, 4))
            pygame.draw.rect(screen, PANTS_COLOR, (sx + 5 - leg_offset, sy + 15, 3, 4))
            pygame.draw.rect(screen, HUNTER_HOOD, (sx + 4 + leg_offset, sy + 18, 3, 2))
            pygame.draw.rect(screen, HUNTER_HOOD, (sx + 5 - leg_offset, sy + 18, 3, 2))
        else:
            pygame.draw.rect(screen, PANTS_COLOR, (sx + 4, sy + 15, 4, 4))
            pygame.draw.rect(screen, HUNTER_HOOD, (sx + 4, sy + 18, 4, 2))

    def _draw_dodge_roll(self, screen: pygame.Surface, sx: int, sy: int, camera: Camera) -> None:
        """Draw rolling animation during dodge."""
        # Calculate roll progress (0 to 1)
        progress = 1 - (self.dodge_timer / DODGE_DURATION)
        
        # Draw afterimage trail (3 ghost images behind)
        dx, dy = self.dodge_direction
        for i in range(3):
            trail_offset = (i + 1) * 8  # Distance behind
            trail_x = sx - dx * trail_offset
            trail_y = sy - dy * trail_offset
            alpha = 80 - i * 25  # Fading trail
            
            # Create translucent trail circle
            trail_surf = pygame.Surface((14, 14))
            trail_surf.set_colorkey((0, 0, 0))
            pygame.draw.circle(trail_surf, SHIRT_COLOR, (7, 7), 6)
            trail_surf.set_alpha(alpha)
            screen.blit(trail_surf, (int(trail_x), int(trail_y + 3)))
        
        # Main rolling ball
        roll_cx = sx + 6
        roll_cy = sy + 10
        
        # Spinning rotation angle
        spin_angle = progress * 720  # Two full rotations during roll
        
        # Draw the rolling ball (player curled up)
        pygame.draw.circle(screen, SHIRT_COLOR, (roll_cx, roll_cy), 8)
        pygame.draw.circle(screen, SKIN_TONE, (roll_cx, roll_cy), 6)
        
        # Add rotating detail to show spin
        detail_angle = math.radians(spin_angle)
        detail_x = roll_cx + math.cos(detail_angle) * 4
        detail_y = roll_cy + math.sin(detail_angle) * 4
        pygame.draw.circle(screen, HAIR_COLOR, (int(detail_x), int(detail_y)), 3)
        
        # Opposite detail for visual spin effect
        detail_x2 = roll_cx + math.cos(detail_angle + math.pi) * 4
        detail_y2 = roll_cy + math.sin(detail_angle + math.pi) * 4
        pygame.draw.circle(screen, PANTS_COLOR, (int(detail_x2), int(detail_y2)), 2)
        
        # Motion blur lines
        blur_length = 12
        for i in range(3):
            blur_offset = i * 3
            blur_alpha = 150 - i * 40
            line_start = (roll_cx - dx * blur_offset, roll_cy - dy * blur_offset)
            line_end = (roll_cx - dx * (blur_offset + blur_length), roll_cy - dy * (blur_offset + blur_length))
            
            blur_surf = pygame.Surface((abs(int(line_end[0] - line_start[0])) + 6, 
                                        abs(int(line_end[1] - line_start[1])) + 6))
            blur_surf.set_colorkey((0, 0, 0))
            pygame.draw.line(blur_surf, (200, 200, 255), 
                           (3, 3), 
                           (abs(int(line_end[0] - line_start[0])) + 3, 
                            abs(int(line_end[1] - line_start[1])) + 3), 2)
            blur_surf.set_alpha(blur_alpha)
            blit_x = min(line_start[0], line_end[0]) - 3
            blit_y = min(line_start[1], line_end[1]) - 3
            screen.blit(blur_surf, (int(blit_x), int(blit_y)))


# =============================================================================
# ENEMY CLASS - GHOSTS, SKELETONS, AND SATAN
# =============================================================================

class Enemy:
    """
    Enemies with distinct behaviors and appearances:
    - Ghost: Floats around erratically, haunting the platform
    - Skeleton: Chases player with rattling bones
    - Boss: Satan himself, lord of hell
    """
    
    def __init__(self, x: float, y: float, enemy_type: EnemyType, wave: int = 1):
        self.enemy_type = enemy_type
        self.x = x
        self.y = y
        self.wave = wave  # Track which wave this enemy was spawned in
        
        if enemy_type == EnemyType.MONKEY:
            self.width = MONKEY_SIZE
            self.height = MONKEY_SIZE
            self.speed = MONKEY_SPEED
            self.damage = MONKEY_DAMAGE
            self.health = MONKEY_HEALTH
            # Monkey animation
            self.anim_frame = 0
            self.anim_timer = 0
            
        elif enemy_type == EnemyType.SNAKE:
            self.width = SNAKE_SEGMENT_SIZE
            self.height = SNAKE_SEGMENT_SIZE
            self.speed = SNAKE_SPEED
            self.damage = SNAKE_DAMAGE
            self.health = SNAKE_HEALTH
            # Snake body segments (positions history)
            self.segments = deque(maxlen=SNAKE_NUM_SEGMENTS)
            for i in range(SNAKE_NUM_SEGMENTS):
                self.segments.append((x, y))
            self.slither_offset = 0
            
        else:  # BOSS
            # Boss scales with wave: bigger and faster each wave
            size_scale = 1.0 + (wave - 1) * 0.15  # 15% bigger each wave
            speed_scale = 1.0 + (wave - 1) * 0.2   # 20% faster each wave
            self.width = int(BOSS_SIZE * size_scale)
            self.height = int(BOSS_SIZE * size_scale)
            self.speed = BOSS_SPEED * speed_scale
            self.damage = BOSS_DAMAGE
            self.health = BOSS_HEALTH + (wave - 1)  # +1 health per wave
            self.tree_block_time = 0  # Frames blocked by tree
            self.destroyed_tree_pos: Tuple[int, int] = (-1, -1)  # Position of destroyed tree
        
        self.move_timer = 0
        self.move_direction = (0, 0)
        self.damage_cooldown = 0
        self.facing_right = True
    
    @property
    def rect(self) -> pygame.Rect:
        if self.enemy_type == EnemyType.SNAKE:
            # Use head position for collision
            return pygame.Rect(self.x - self.width//2, self.y - self.height//2, 
                             self.width + 2, self.height + 2)
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def center(self) -> Tuple[float, float]:
        if self.enemy_type == EnemyType.SNAKE:
            return (self.x, self.y)
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def update(self, player: Player) -> None:
        """Update enemy AI and animation."""
        self.damage_cooldown = max(0, self.damage_cooldown - 1)
        
        if self.enemy_type == EnemyType.MONKEY:
            self._update_monkey(player)
        elif self.enemy_type == EnemyType.SNAKE:
            self._update_snake(player)
        else:
            self._update_boss(player)
    
    def _update_monkey(self, player: Player) -> None:
        """Erratic monkey movement."""
        old_x, old_y = self.x, self.y
        
        self.anim_timer += 1
        if self.anim_timer >= 10:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2
        
        self.move_timer -= 1
        if self.move_timer <= 0:
            # Sometimes move toward player, sometimes random
            if random.random() < 0.1:
                px, py = player.center
                dx = px - self.center[0]
                dy = py - self.center[1]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    self.move_direction = (dx/dist, dy/dist)
            else:
                angle = random.uniform(0, 2 * math.pi)
                self.move_direction = (math.cos(angle), math.sin(angle))
            self.move_timer = random.randint(20, 60)
        
        move_dx = self.move_direction[0] * self.speed
        move_dy = self.move_direction[1] * self.speed
        
        self.x += move_dx
        self.y += move_dy
        self.facing_right = self.move_direction[0] >= 0
        
        self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
        self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
        
        # Check tree collision - try to navigate around
        if check_tree_collision(self.rect):
            # Try moving only on X axis
            self.x, self.y = old_x + move_dx, old_y
            self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
            if not check_tree_collision(self.rect):
                return  # X-only movement worked
            
            # Try moving only on Y axis
            self.x, self.y = old_x, old_y + move_dy
            self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
            if not check_tree_collision(self.rect):
                return  # Y-only movement worked
            
            # Can't slide, pick a new direction to go around
            self.x, self.y = old_x, old_y
            # Steer perpendicular to current direction (randomly left or right)
            perp_angle = math.atan2(self.move_direction[1], self.move_direction[0])
            perp_angle += math.pi / 2 if random.random() < 0.5 else -math.pi / 2
            self.move_direction = (math.cos(perp_angle), math.sin(perp_angle))
            self.move_timer = random.randint(10, 30)
    
    def _update_snake(self, player: Player) -> None:
        """Slithering snake movement toward player."""
        old_x, old_y = self.x, self.y
        
        self.slither_offset += 0.3
        
        px, py = player.center
        dx = px - self.x
        dy = py - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        move_x, move_y = 0, 0
        if dist > 0:
            # Add sinusoidal slither to movement
            slither = math.sin(self.slither_offset) * 0.5
            perp_x = -dy / dist
            perp_y = dx / dist
            
            move_x = (dx / dist) * self.speed + perp_x * slither
            move_y = (dy / dist) * self.speed + perp_y * slither
            
            self.x += move_x
            self.y += move_y
        
        self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT))
        self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM))
        
        # Check tree collision - try to navigate around
        if check_tree_collision(self.rect):
            # Try moving only on X axis
            self.x, self.y = old_x + move_x, old_y
            self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT))
            if not check_tree_collision(self.rect):
                self.segments.appendleft((self.x, self.y))
                return
            
            # Try moving only on Y axis
            self.x, self.y = old_x, old_y + move_y
            self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM))
            if not check_tree_collision(self.rect):
                self.segments.appendleft((self.x, self.y))
                return
            
            # Try steering around - move perpendicular to player direction
            if dist > 0:
                # Choose perpendicular direction based on which side has more space
                perp_x = -dy / dist
                perp_y = dx / dist
                # Try one perpendicular direction
                self.x = old_x + perp_x * self.speed
                self.y = old_y + perp_y * self.speed
                self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT))
                self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM))
                if not check_tree_collision(self.rect):
                    self.segments.appendleft((self.x, self.y))
                    return
                # Try the other perpendicular direction
                self.x = old_x - perp_x * self.speed
                self.y = old_y - perp_y * self.speed
                self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT))
                self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM))
                if not check_tree_collision(self.rect):
                    self.segments.appendleft((self.x, self.y))
                    return
            
            # Can't move at all, stay in place
            self.x, self.y = old_x, old_y
        
        # Update body segments (follow the head)
        self.segments.appendleft((self.x, self.y))
    
    def _update_boss(self, player: Player) -> None:
        """Boss pursues player slowly."""
        old_x, old_y = self.x, self.y
        
        px, py = player.center
        ex, ey = self.center
        dx = px - ex
        dy = py - ey
        dist = math.sqrt(dx * dx + dy * dy)
        
        move_x, move_y = 0, 0
        if dist > 0:
            move_x = (dx / dist) * self.speed
            move_y = (dy / dist) * self.speed
            self.x += move_x
            self.y += move_y
            self.facing_right = dx >= 0
        
        self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
        self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
        
        # Check if direct movement toward player is blocked by tree
        direct_blocked = check_tree_collision(self.rect)
        intended_rect = pygame.Rect(old_x + move_x, old_y + move_y, self.width, self.height)
        blocking_tree = get_blocking_tree_index(intended_rect) if direct_blocked else -1
        
        # Check tree collision - try to navigate around
        if direct_blocked:
            # Try moving only on X axis
            self.x, self.y = old_x + move_x, old_y
            self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
            if not check_tree_collision(self.rect):
                # Moved but still blocked from direct path - keep counting
                self.tree_block_time += 1
                if self.tree_block_time >= 60 and blocking_tree >= 0:
                    self.destroyed_tree_pos = destroy_tree(blocking_tree)
                    self.tree_block_time = 0
                return
            
            # Try moving only on Y axis
            self.x, self.y = old_x, old_y + move_y
            self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
            if not check_tree_collision(self.rect):
                # Moved but still blocked from direct path - keep counting
                self.tree_block_time += 1
                if self.tree_block_time >= 60 and blocking_tree >= 0:
                    self.destroyed_tree_pos = destroy_tree(blocking_tree)
                    self.tree_block_time = 0
                return
            
            # Try steering around - move perpendicular to player direction
            if dist > 0:
                perp_x = -dy / dist
                perp_y = dx / dist
                # Try one perpendicular direction
                self.x = old_x + perp_x * self.speed
                self.y = old_y + perp_y * self.speed
                self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
                self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
                if not check_tree_collision(self.rect):
                    # Moved but still blocked from direct path - keep counting
                    self.tree_block_time += 1
                    if self.tree_block_time >= 60 and blocking_tree >= 0:
                        self.destroyed_tree_pos = destroy_tree(blocking_tree)
                        self.tree_block_time = 0
                    return
                # Try the other perpendicular direction
                self.x = old_x - perp_x * self.speed
                self.y = old_y - perp_y * self.speed
                self.x = max(ISLAND_LEFT, min(self.x, ISLAND_RIGHT - self.width))
                self.y = max(ISLAND_TOP, min(self.y, ISLAND_BOTTOM - self.height))
                if not check_tree_collision(self.rect):
                    # Moved but still blocked from direct path - keep counting
                    self.tree_block_time += 1
                    if self.tree_block_time >= 60 and blocking_tree >= 0:
                        self.destroyed_tree_pos = destroy_tree(blocking_tree)
                        self.tree_block_time = 0
                    return
            
            # Can't move at all - boss is completely stuck
            self.x, self.y = old_x, old_y
            self.tree_block_time += 1
            
            # If blocked for more than 1 second (60 frames), destroy the tree
            if self.tree_block_time >= 60 and blocking_tree >= 0:
                self.destroyed_tree_pos = destroy_tree(blocking_tree)
                self.tree_block_time = 0
        else:
            self.tree_block_time = 0  # Direct path is clear
    
    def take_damage(self, amount: int = 1) -> bool:
        self.health -= amount
        return self.health <= 0
    
    def can_damage_player(self) -> bool:
        return self.damage_cooldown == 0
    
    def reset_damage_cooldown(self) -> None:
        self.damage_cooldown = 60
    
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw enemy based on type."""
        if self.enemy_type == EnemyType.MONKEY:
            self._draw_monkey(screen, camera)
        elif self.enemy_type == EnemyType.SNAKE:
            self._draw_snake(screen, camera)
        else:
            self._draw_boss(screen, camera)
    
    def _draw_monkey(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw a floating ghost."""
        screen_rect = camera.apply(self.rect)
        sx, sy = int(screen_rect.x), int(screen_rect.y)
        
        # Floating animation
        time = pygame.time.get_ticks()
        float_offset = int(math.sin(time / 200 + self.x) * 2)
        bob = self.anim_frame
        
        # Ghost body (semi-transparent effect with layered shapes)
        # Main body - rounded top, wavy bottom
        pygame.draw.ellipse(screen, GHOST_BODY, (sx + 1, sy + float_offset, 12, 10))
        pygame.draw.rect(screen, GHOST_BODY, (sx + 1, sy + 5 + float_offset, 12, 8))
        
        # Wavy bottom tail
        wave_offset = bob * 2
        pygame.draw.polygon(screen, GHOST_BODY, [
            (sx + 1, sy + 12 + float_offset),
            (sx + 3 + wave_offset, sy + 16 + float_offset),
            (sx + 7, sy + 13 + float_offset),
            (sx + 11 - wave_offset, sy + 16 + float_offset),
            (sx + 13, sy + 12 + float_offset)
        ])
        
        # Inner glow/highlight
        pygame.draw.ellipse(screen, GHOST_GLOW, (sx + 3, sy + 2 + float_offset, 8, 6))
        
        # Hollow dark eyes
        pygame.draw.ellipse(screen, BLACK, (sx + 3, sy + 4 + float_offset, 3, 4))
        pygame.draw.ellipse(screen, BLACK, (sx + 8, sy + 4 + float_offset, 3, 4))
        
        # Spooky mouth (wavy)
        pygame.draw.ellipse(screen, BLACK, (sx + 5, sy + 9 + float_offset, 4, 3))
    
    def _draw_snake(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw a chasing skeleton."""
        # Draw bone segments from tail to head (spine)
        segments_list = list(self.segments)
        for i, (seg_x, seg_y) in enumerate(reversed(segments_list)):
            screen_x, screen_y = camera.apply_pos(seg_x, seg_y)
            
            # Alternating vertebrae pattern
            if i % 2 == 0:
                # Larger vertebra
                pygame.draw.circle(screen, BONE_WHITE, (int(screen_x), int(screen_y)), 4)
                pygame.draw.circle(screen, BONE_DARK, (int(screen_x), int(screen_y)), 2)
            else:
                # Smaller connecting bone
                pygame.draw.circle(screen, BONE_DARK, (int(screen_x), int(screen_y)), 3)
            
            # Rib bones on every other segment
            if i % 3 == 0 and i > 0:
                pygame.draw.line(screen, BONE_WHITE, 
                               (int(screen_x) - 4, int(screen_y)),
                               (int(screen_x) + 4, int(screen_y)), 2)
        
        # Draw skull (head)
        head_x, head_y = camera.apply_pos(self.x, self.y)
        hx, hy = int(head_x), int(head_y)
        
        # Skull shape
        pygame.draw.ellipse(screen, BONE_WHITE, (hx - 6, hy - 5, 12, 10))
        pygame.draw.ellipse(screen, BONE_WHITE, (hx - 5, hy + 2, 10, 6))  # Jaw
        
        # Eye sockets (dark hollow)
        pygame.draw.ellipse(screen, BONE_SOCKET, (hx - 4, hy - 2, 4, 5))
        pygame.draw.ellipse(screen, BONE_SOCKET, (hx + 1, hy - 2, 4, 5))
        
        # Glowing red eyes inside sockets
        pygame.draw.circle(screen, RED, (hx - 2, hy), 1)
        pygame.draw.circle(screen, RED, (hx + 3, hy), 1)
        
        # Nose hole
        pygame.draw.polygon(screen, BONE_SOCKET, [
            (hx, hy + 2), (hx - 1, hy + 4), (hx + 1, hy + 4)
        ])
        
        # Teeth
        for t in range(-3, 4, 2):
            pygame.draw.rect(screen, BONE_WHITE, (hx + t, hy + 5, 2, 2))
    
    def _draw_boss(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw Satan, the lord of hell."""
        screen_rect = camera.apply(self.rect)
        sx, sy = int(screen_rect.x), int(screen_rect.y)
        w, h = int(screen_rect.width), int(screen_rect.height)
        
        # Hellfire aura (animated)
        time = pygame.time.get_ticks()
        for i in range(3):
            flicker = int(math.sin(time / 100 + i) * 3)
            aura_color = (200 + flicker * 5, 60 + i * 20, 20)
            pygame.draw.ellipse(screen, aura_color, 
                              (sx + 2 - i*2, sy + h//2 - i*3 + flicker, w - 4 + i*4, h//2 + i*6))
        
        # Main body (muscular red demon)
        pygame.draw.ellipse(screen, SATAN_RED, (sx + 4, sy + 10, w - 8, h - 14))
        pygame.draw.ellipse(screen, SATAN_DARK, (sx + 6, sy + 12, w - 12, h - 18))  # Shading
        
        # Head
        pygame.draw.circle(screen, SATAN_RED, (sx + w//2, sy + 12), 10)
        pygame.draw.circle(screen, SATAN_DARK, (sx + w//2 + 2, sy + 14), 6)  # Shading
        
        # Horns (curved evil horns)
        # Left horn
        pygame.draw.polygon(screen, SATAN_HORN, [
            (sx + w//2 - 8, sy + 6),
            (sx + w//2 - 14, sy - 6),
            (sx + w//2 - 10, sy - 4),
            (sx + w//2 - 6, sy + 4)
        ])
        # Right horn
        pygame.draw.polygon(screen, SATAN_HORN, [
            (sx + w//2 + 8, sy + 6),
            (sx + w//2 + 14, sy - 6),
            (sx + w//2 + 10, sy - 4),
            (sx + w//2 + 6, sy + 4)
        ])
        
        # Glowing evil eyes
        pygame.draw.ellipse(screen, YELLOW, (sx + w//2 - 6, sy + 8, 5, 4))
        pygame.draw.ellipse(screen, YELLOW, (sx + w//2 + 2, sy + 8, 5, 4))
        pygame.draw.ellipse(screen, RED, (sx + w//2 - 5, sy + 9, 3, 2))
        pygame.draw.ellipse(screen, RED, (sx + w//2 + 3, sy + 9, 3, 2))
        
        # Evil grin with fangs
        pygame.draw.arc(screen, BLACK, (sx + w//2 - 6, sy + 14, 12, 6), 3.4, 6.0, 2)
        # Fangs
        pygame.draw.polygon(screen, WHITE, [
            (sx + w//2 - 4, sy + 17), (sx + w//2 - 2, sy + 20), (sx + w//2, sy + 17)
        ])
        pygame.draw.polygon(screen, WHITE, [
            (sx + w//2 + 1, sy + 17), (sx + w//2 + 3, sy + 20), (sx + w//2 + 5, sy + 17)
        ])
        
        # Muscular arms
        pygame.draw.ellipse(screen, SATAN_RED, (sx - 2, sy + 14, 10, 14))
        pygame.draw.ellipse(screen, SATAN_RED, (sx + w - 8, sy + 14, 10, 14))
        # Claws
        for cx in [-1, 2, 5]:
            pygame.draw.line(screen, SATAN_HORN, (sx + cx, sy + 28), (sx + cx - 2, sy + 32), 2)
            pygame.draw.line(screen, SATAN_HORN, (sx + w - 6 + cx, sy + 28), (sx + w - 4 + cx, sy + 32), 2)
        
        # Legs with hooves
        pygame.draw.ellipse(screen, SATAN_RED, (sx + 6, sy + h - 12, 8, 12))
        pygame.draw.ellipse(screen, SATAN_RED, (sx + w - 14, sy + h - 12, 8, 12))
        # Hooves
        pygame.draw.ellipse(screen, SATAN_HORN, (sx + 5, sy + h - 3, 10, 4))
        pygame.draw.ellipse(screen, SATAN_HORN, (sx + w - 15, sy + h - 3, 10, 4))
        
        # Pointed tail
        tail_wave = int(math.sin(time / 150) * 4)
        pygame.draw.lines(screen, SATAN_RED, False, [
            (sx + w//2, sy + h - 8),
            (sx + w + 5 + tail_wave, sy + h - 15),
            (sx + w + 10, sy + h - 10 + tail_wave)
        ], 3)
        # Tail point
        pygame.draw.polygon(screen, SATAN_DARK, [
            (sx + w + 8, sy + h - 12 + tail_wave),
            (sx + w + 15, sy + h - 8 + tail_wave),
            (sx + w + 10, sy + h - 5 + tail_wave)
        ])
        
        # Health bar
        bar_width = w
        bar_height = 3
        health_ratio = self.health / BOSS_HEALTH
        pygame.draw.rect(screen, RED, (sx, sy - 10, bar_width, bar_height))
        pygame.draw.rect(screen, LAVA_BRIGHT, (sx, sy - 10, int(bar_width * health_ratio), bar_height))


# =============================================================================
# ARROW CLASS
# =============================================================================

class Arrow:
    """Projectile fired by the bow."""
    
    def __init__(self, x: float, y: float, dx: float, dy: float):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.width = 4
        self.height = 4
        self.lifetime = ARROW_LIFETIME
        self.active = True
    
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self) -> None:
        """Move arrow and check lifetime."""
        self.x += self.dx * ARROW_SPEED
        self.y += self.dy * ARROW_SPEED
        self.lifetime -= 1
        
        # Deactivate if out of bounds or lifetime expired
        if (self.lifetime <= 0 or self.x < 0 or self.x > MAP_WIDTH or 
            self.y < 0 or self.y > MAP_HEIGHT):
            self.active = False
    
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw arrow."""
        sx, sy = camera.apply_pos(self.x, self.y)
        sx, sy = int(sx), int(sy)
        
        # Calculate arrow tip position based on direction
        angle = math.atan2(self.dy, self.dx)
        tip_x = sx + int(math.cos(angle) * 6)
        tip_y = sy + int(math.sin(angle) * 6)
        tail_x = sx - int(math.cos(angle) * 4)
        tail_y = sy - int(math.sin(angle) * 4)
        
        # Arrow shaft
        pygame.draw.line(screen, BROWN, (tail_x, tail_y), (tip_x, tip_y), 2)
        # Arrow head
        pygame.draw.circle(screen, GREY, (tip_x, tip_y), 2)


class Bomb:
    """Thrown bomb that explodes after a delay."""
    
    def __init__(self, x: float, y: float, dx: float, dy: float, damage: int, explosion_range: int):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.explosion_range = explosion_range
        self.width = 8
        self.height = 8
        self.flight_time = BOMB_FLIGHT_TIME
        self.active = True
        self.exploded = False
    
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
    
    def update(self) -> None:
        """Move bomb and count down to explosion."""
        if not self.exploded:
            self.x += self.dx * BOMB_SPEED
            self.y += self.dy * BOMB_SPEED
            # Slow down over time
            self.dx *= 0.95
            self.dy *= 0.95
            self.flight_time -= 1
            
            if self.flight_time <= 0:
                self.exploded = True
    
    def get_explosion_rect(self) -> pygame.Rect:
        """Get the area affected by explosion."""
        return pygame.Rect(
            self.x - self.explosion_range,
            self.y - self.explosion_range,
            self.explosion_range * 2,
            self.explosion_range * 2
        )
    
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw bomb."""
        sx, sy = camera.apply_pos(self.x, self.y)
        sx, sy = int(sx), int(sy)
        
        if not self.exploded:
            # Bomb body (dark grey sphere)
            pygame.draw.circle(screen, (50, 50, 50), (sx, sy), 5)
            # Fuse (flashing when about to explode)
            fuse_color = ORANGE if self.flight_time % 4 < 2 else RED
            pygame.draw.line(screen, fuse_color, (sx, sy - 5), (sx + 2, sy - 8), 2)
            # Spark
            if self.flight_time % 6 < 3:
                pygame.draw.circle(screen, YELLOW, (sx + 2, sy - 9), 2)


# =============================================================================
# PARTICLE CLASS - For dramatic effects
# =============================================================================

class Particle:
    """A single particle for visual effects."""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], 
                 dx: float = 0, dy: float = 0, lifetime: int = 30):
        self.x = x
        self.y = y
        self.color = color
        self.dx = dx
        self.dy = dy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = 4
    
    def update(self) -> bool:
        """Update particle. Returns False when dead."""
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.1  # Gravity
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw particle with fade effect."""
        alpha_ratio = self.lifetime / self.max_lifetime
        size = max(1, int(self.size * alpha_ratio))
        sx, sy = camera.apply_pos(self.x, self.y)
        pygame.draw.circle(screen, self.color, (int(sx), int(sy)), size)


class FloatingText:
    """Floating score text that rises and fades."""
    
    def __init__(self, x: float, y: float, text: str, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 45  # Frames to display
        self.max_lifetime = 45
        self.dy = -1.5  # Rise speed
    
    def update(self) -> bool:
        """Update floating text. Returns False when expired."""
        self.y += self.dy
        self.dy *= 0.95  # Slow down
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen: pygame.Surface, camera: Camera, font: pygame.font.Font) -> None:
        """Draw floating text with fade effect."""
        alpha_ratio = self.lifetime / self.max_lifetime
        sx, sy = camera.apply_pos(self.x, self.y)
        
        # Create text surface
        text_surf = font.render(self.text, False, self.color)
        
        # Apply alpha by creating a copy surface
        alpha_surf = pygame.Surface(text_surf.get_size())
        alpha_surf.fill((0, 0, 0))
        alpha_surf.set_colorkey((0, 0, 0))
        alpha_surf.blit(text_surf, (0, 0))
        alpha_surf.set_alpha(int(255 * alpha_ratio))
        
        # Center the text
        tx = int(sx) - text_surf.get_width() // 2
        ty = int(sy) - text_surf.get_height() // 2
        screen.blit(alpha_surf, (tx, ty))


# =============================================================================
# ITEM CLASS
# =============================================================================

class Item:
    """Collectible items."""
    
    def __init__(self, x: float, y: float, item_type: ItemType):
        self.item_type = item_type
        self.x = x
        self.y = y
        
        if item_type == ItemType.SWORD:
            self.width = SWORD_SIZE[0]
            self.height = SWORD_SIZE[1]
        elif item_type == ItemType.BOW:
            self.width = BOW_SIZE[0]
            self.height = BOW_SIZE[1]
        elif item_type == ItemType.BOMB:
            self.width = BOMB_SIZE[0]
            self.height = BOMB_SIZE[1]
        elif item_type == ItemType.LOOT_BAG:
            self.width = LOOT_BAG_SIZE
            self.height = LOOT_BAG_SIZE
        else:
            self.width = FOOD_SIZE
            self.height = FOOD_SIZE
        
        self.bob_offset = random.uniform(0, math.pi * 2)
    
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_heal_amount(self) -> int:
        if self.item_type == ItemType.APPLE:
            return 10
        elif self.item_type == ItemType.BANANA:
            return 20
        elif self.item_type == ItemType.DURIAN:
            return 50
        return 0
    
    def draw(self, screen: pygame.Surface, camera: Camera, time: int) -> None:
        """Draw item with slight bobbing animation."""
        bob = math.sin(time * 0.1 + self.bob_offset) * 1
        screen_rect = camera.apply(self.rect)
        sx, sy = int(screen_rect.x), int(screen_rect.y + bob)
        
        if self.item_type == ItemType.SWORD:
            # Pixel art sword
            pygame.draw.rect(screen, GREY, (sx + 2, sy, 2, 10))  # Blade
            pygame.draw.rect(screen, DARK_BROWN, (sx + 1, sy + 10, 4, 4))  # Handle
            pygame.draw.rect(screen, YELLOW, (sx, sy + 9, 6, 2))  # Guard
            # Shining sparkles
            sparkle_phase = (time // 6) % 6
            sparkle_positions = [
                (sx - 2, sy - 2), (sx + 6, sy - 1), (sx + 7, sy + 5),
                (sx - 1, sy + 8), (sx + 5, sy + 12), (sx - 2, sy + 4)
            ]
            for i in range(2):
                idx = (sparkle_phase + i * 3) % len(sparkle_positions)
                spx, spy = sparkle_positions[idx]
                pygame.draw.line(screen, WHITE, (spx, spy - 1), (spx, spy + 1), 1)
                pygame.draw.line(screen, WHITE, (spx - 1, spy), (spx + 1, spy), 1)
        
        elif self.item_type == ItemType.BOW:
            # Pixel art bow - curved shape
            # Bow body (curved arc)
            pygame.draw.arc(screen, BROWN, (sx, sy, 10, 12), -1.5, 1.5, 2)
            # Bow string
            pygame.draw.line(screen, WHITE, (sx + 8, sy + 1), (sx + 8, sy + 11), 1)
            # Grip
            pygame.draw.rect(screen, DARK_BROWN, (sx + 2, sy + 5, 3, 3))
            # Shining sparkles
            sparkle_phase = (time // 6) % 6
            sparkle_positions = [
                (sx - 2, sy), (sx + 11, sy + 2), (sx + 12, sy + 9),
                (sx - 1, sy + 11), (sx + 5, sy - 2), (sx + 10, sy + 6)
            ]
            for i in range(2):
                idx = (sparkle_phase + i * 3) % len(sparkle_positions)
                spx, spy = sparkle_positions[idx]
                pygame.draw.line(screen, WHITE, (spx, spy - 1), (spx, spy + 1), 1)
                pygame.draw.line(screen, WHITE, (spx - 1, spy), (spx + 1, spy), 1)
        
        elif self.item_type == ItemType.BOMB:
            # Bomb pickup - dark sphere with fuse
            cx, cy = sx + 5, sy + 5
            # Bomb body
            pygame.draw.circle(screen, (40, 40, 40), (cx, cy), 5)
            pygame.draw.circle(screen, (80, 80, 80), (cx - 1, cy - 1), 2)  # Highlight
            # Fuse
            pygame.draw.line(screen, BROWN, (cx, cy - 5), (cx + 2, cy - 8), 2)
            # Spark (animated)
            if (time // 4) % 2 == 0:
                pygame.draw.circle(screen, ORANGE, (cx + 2, cy - 9), 2)
            else:
                pygame.draw.circle(screen, YELLOW, (cx + 2, cy - 9), 2)
            # Sparkles
            sparkle_phase = (time // 6) % 4
            sparkle_positions = [(cx - 6, cy - 2), (cx + 6, cy - 2), (cx - 4, cy + 5), (cx + 4, cy + 5)]
            spx, spy = sparkle_positions[sparkle_phase]
            pygame.draw.line(screen, WHITE, (spx, spy - 1), (spx, spy + 1), 1)
            pygame.draw.line(screen, WHITE, (spx - 1, spy), (spx + 1, spy), 1)
            
        elif self.item_type == ItemType.APPLE:
            # Empty heart (3D outline) - small heal
            # Dark shadow/depth layer
            shadow = (60, 30, 40)
            pygame.draw.circle(screen, shadow, (sx + 4, sy + 4), 4)
            pygame.draw.circle(screen, shadow, (sx + 8, sy + 4), 4)
            pygame.draw.polygon(screen, shadow, [
                (sx, sy + 5), (sx + 12, sy + 5), (sx + 6, sy + 12)
            ])
            # Inner dark hollow
            inner_dark = (30, 20, 25)
            pygame.draw.circle(screen, inner_dark, (sx + 4, sy + 3), 3)
            pygame.draw.circle(screen, inner_dark, (sx + 8, sy + 3), 3)
            pygame.draw.polygon(screen, inner_dark, [
                (sx + 1, sy + 4), (sx + 11, sy + 4), (sx + 6, sy + 10)
            ])
            # Highlight rim on top-left
            rim_light = (140, 70, 90)
            pygame.draw.arc(screen, rim_light, (sx + 1, sy, 6, 6), 0.5, 2.5, 1)
            pygame.draw.arc(screen, rim_light, (sx + 5, sy, 6, 6), 0.5, 2.0, 1)
            
        elif self.item_type == ItemType.BANANA:
            # Half-full heart (3D) - medium heal
            # Shadow base
            shadow = (50, 25, 35)
            pygame.draw.circle(screen, shadow, (sx + 4, sy + 4), 4)
            pygame.draw.circle(screen, shadow, (sx + 8, sy + 4), 4)
            pygame.draw.polygon(screen, shadow, [
                (sx, sy + 5), (sx + 12, sy + 5), (sx + 6, sy + 12)
            ])
            # Empty right half (dark hollow)
            empty_dark = (40, 25, 30)
            pygame.draw.circle(screen, empty_dark, (sx + 8, sy + 3), 3)
            pygame.draw.polygon(screen, empty_dark, [
                (sx + 6, sy + 4), (sx + 11, sy + 4), (sx + 6, sy + 10)
            ])
            # Filled left half - main color
            heart_color = (220, 60, 90)
            pygame.draw.circle(screen, heart_color, (sx + 4, sy + 3), 3)
            pygame.draw.polygon(screen, heart_color, [
                (sx + 1, sy + 4), (sx + 6, sy + 4), (sx + 6, sy + 10)
            ])
            # Shading on filled part (darker bottom-right)
            heart_dark = (160, 40, 65)
            pygame.draw.circle(screen, heart_dark, (sx + 5, sy + 4), 2)
            # Bright highlight on top-left
            highlight = (255, 140, 170)
            pygame.draw.circle(screen, highlight, (sx + 3, sy + 2), 1)
            pygame.draw.rect(screen, (255, 200, 210), (sx + 2, sy + 1, 1, 1))
            # Shine
            pygame.draw.rect(screen, WHITE, (sx + 2, sy + 2, 1, 1))
            
        elif self.item_type == ItemType.DURIAN:
            # Full heart (3D) - heals the most!
            # Shadow base
            shadow = (120, 30, 50)
            pygame.draw.circle(screen, shadow, (sx + 4, sy + 4), 4)
            pygame.draw.circle(screen, shadow, (sx + 8, sy + 4), 4)
            pygame.draw.polygon(screen, shadow, [
                (sx, sy + 5), (sx + 12, sy + 5), (sx + 6, sy + 12)
            ])
            # Main heart body
            heart_color = (230, 60, 100)
            pygame.draw.circle(screen, heart_color, (sx + 4, sy + 3), 3)
            pygame.draw.circle(screen, heart_color, (sx + 8, sy + 3), 3)
            pygame.draw.polygon(screen, heart_color, [
                (sx + 1, sy + 4), (sx + 11, sy + 4), (sx + 6, sy + 10)
            ])
            # Darker shading (bottom-right areas)
            heart_dark = (180, 40, 70)
            pygame.draw.circle(screen, heart_dark, (sx + 9, sy + 4), 2)
            pygame.draw.polygon(screen, heart_dark, [
                (sx + 6, sy + 6), (sx + 9, sy + 5), (sx + 6, sy + 9)
            ])
            # Mid-tone transition
            heart_mid = (210, 50, 85)
            pygame.draw.circle(screen, heart_mid, (sx + 5, sy + 4), 2)
            # Bright highlights (top-left)
            highlight = (255, 130, 160)
            pygame.draw.circle(screen, highlight, (sx + 3, sy + 2), 2)
            pygame.draw.circle(screen, highlight, (sx + 7, sy + 2), 1)
            # Shine spots
            pygame.draw.rect(screen, (255, 200, 215), (sx + 2, sy + 1, 2, 1))
            pygame.draw.rect(screen, WHITE, (sx + 2, sy + 2, 1, 1))
            pygame.draw.rect(screen, WHITE, (sx + 7, sy + 1, 1, 1))
            
        elif self.item_type == ItemType.LOOT_BAG:
            # Shining treasure crate
            crate_color = (139, 90, 43)  # Wood brown
            crate_dark = (101, 67, 33)   # Darker wood
            gold = (255, 215, 0)
            
            # Main crate body
            pygame.draw.rect(screen, crate_color, (sx, sy + 2, 12, 10))
            # Top of crate (lid)
            pygame.draw.rect(screen, crate_dark, (sx - 1, sy, 14, 3))
            # Wood planks detail
            pygame.draw.line(screen, crate_dark, (sx, sy + 5), (sx + 11, sy + 5), 1)
            pygame.draw.line(screen, crate_dark, (sx + 6, sy + 2), (sx + 6, sy + 11), 1)
            # Gold lock/clasp
            pygame.draw.rect(screen, gold, (sx + 4, sy + 1, 4, 3))
            pygame.draw.rect(screen, (200, 170, 0), (sx + 5, sy + 2, 2, 1))
            
            # Shining sparkles that cycle
            sparkle_phase = (time // 5) % 8
            sparkle_positions = [
                (sx - 2, sy - 2), (sx + 12, sy - 1), (sx + 13, sy + 8),
                (sx - 1, sy + 10), (sx + 6, sy - 3), (sx + 14, sy + 4),
                (sx - 3, sy + 5), (sx + 8, sy + 13)
            ]
            # Draw 2-3 sparkles at a time
            for i in range(3):
                idx = (sparkle_phase + i * 3) % len(sparkle_positions)
                spx, spy = sparkle_positions[idx]
                # Star sparkle shape
                pygame.draw.line(screen, WHITE, (spx, spy - 2), (spx, spy + 2), 1)
                pygame.draw.line(screen, WHITE, (spx - 2, spy), (spx + 2, spy), 1)
                # Yellow glow on corners
                pygame.draw.rect(screen, YELLOW, (spx - 1, spy - 1, 1, 1))
                pygame.draw.rect(screen, YELLOW, (spx + 1, spy + 1, 1, 1))


# =============================================================================
# GAME MANAGER CLASS
# =============================================================================

class GameManager:
    """Main game controller with retro rendering and resizable window."""
    
    MAX_HIGH_SCORES = 10
    
    def __init__(self):
        global TREE_RECTS
        
        # Start in fullscreen mode by default
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        info = pygame.display.Info()
        self.window_width = info.current_w
        self.window_height = info.current_h
        pygame.display.set_caption("Hell Survivor")
        
        # Internal rendering surface (low-res for retro feel)
        self.game_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        
        # CRT filter
        self.crt_filter = CRTFilter(self.window_width, self.window_height)
        
        # Fullscreen state
        self.is_fullscreen = True
        
        self.clock = pygame.time.Clock()
        self.frame_count = 0
        
        # Retro-style fonts - use SysFont for better compatibility
        self.font = pygame.font.SysFont("arial", 14)
        self.big_font = pygame.font.SysFont("arial", 36, bold=True)
        
        # Sound manager
        self.sound = SoundManager()
        
        # Initialize tree collision rects
        TREE_RECTS = get_tree_rects()
        
        # High scores (in memory only)
        self.high_scores: List[dict] = []
        
        # Show instructions screen first
        self.show_instructions = True
        self.running = True
        
        self.reset_game()
    
    def add_high_score(self, score: int, time: int, wave: int, weapon: str) -> int:
        """Add a new high score. Returns rank (1-10) or 0 if not top 10."""
        entry = {"score": score, "time": time, "wave": wave, "weapon": weapon}
        self.high_scores.append(entry)
        # Sort by score descending, then time descending
        self.high_scores.sort(key=lambda x: (x["score"], x["time"]), reverse=True)
        # Keep only top 10
        self.high_scores = self.high_scores[:self.MAX_HIGH_SCORES]
        
        # Find rank of this score
        for i, hs in enumerate(self.high_scores):
            if hs["score"] == score and hs["time"] == time and hs["wave"] == wave and hs.get("weapon") == weapon:
                return i + 1
        return 0
    
    def toggle_fullscreen(self) -> None:
        """Toggle between fullscreen and windowed mode."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            info = pygame.display.Info()
            self.window_width = info.current_w
            self.window_height = info.current_h
        else:
            self.window_width = DEFAULT_WINDOW_WIDTH
            self.window_height = DEFAULT_WINDOW_HEIGHT
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height), 
                pygame.RESIZABLE
            )
        self.crt_filter.resize(self.window_width, self.window_height)
    
    def handle_resize(self, width: int, height: int) -> None:
        """Handle window resize event."""
        self.window_width = width
        self.window_height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.crt_filter.resize(width, height)
    
    def reset_game(self) -> None:
        """Reset all game state."""
        global TREE_POSITIONS, TREE_RECTS, PLATFORM_EDGE_POINTS, PLATFORM_INNER_POINTS
        
        # Generate new random tree positions
        TREE_POSITIONS = generate_tree_positions()
        TREE_RECTS = get_tree_rects()
        
        # Generate irregular platform edge
        PLATFORM_EDGE_POINTS, PLATFORM_INNER_POINTS = generate_platform_edge()
        
        self.camera = Camera(INTERNAL_WIDTH, INTERNAL_HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        self.player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.enemies: List[Enemy] = []
        self.items: List[Item] = []
        self.arrows: List[Arrow] = []  # Active arrows
        self.bombs: List[Bomb] = []  # Active bombs
        
        # Spawn weapons around player - triangle formation
        # Sword on the left
        sword_x = self.player.x - 60
        sword_y = self.player.y
        self.items.append(Item(sword_x, sword_y, ItemType.SWORD))
        
        # Bow on the right
        bow_x = self.player.x + 60
        bow_y = self.player.y
        self.items.append(Item(bow_x, bow_y, ItemType.BOW))
        
        # Bomb hidden in lower-left corner (secret weapon!)
        bomb_x = ISLAND_LEFT + 20
        bomb_y = ISLAND_BOTTOM - 30
        self.items.append(Item(bomb_x, bomb_y, ItemType.BOMB))
        
        # Particles for visual effects
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []
        
        for _ in range(4):
            self.spawn_food()
        
        self.game_over = False
        self.running = True
        self.start_time = pygame.time.get_ticks()
        self.enemies_killed = 0
        self.total_kills = 0  # Total kills across all waves
        self.score = 0  # Score system: 5 monkey, 10 snake, 100 boss
        
        # Wave system
        self.current_wave = 1
        self.wave_active = False  # True when bosses are spawned
        self.bosses_remaining = 0
        self.wave_start_time = pygame.time.get_ticks()
        self.wave_kills = 0  # Kills since wave ended
        self.wave_complete = False  # True after all bosses in wave are dead
        self.loot_dropped_this_wave = False
        
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.last_food_spawn = pygame.time.get_ticks()
        
        self.upgrade_message = ""
        self.upgrade_message_timer = 0
        
        # Track used upgrades to prevent repeats
        self.used_upgrades: set = set()
        self.boss_kills = 0  # Track boss kills for first upgrade logic
        
        # High score tracking
        self.score_saved = False
        self.last_rank = 0
        self.final_time = 0  # Time when game ended
    
    def respawn(self) -> None:
        """Respawn player keeping wave progress and upgrades."""
        # Save current progress
        saved_wave = self.current_wave
        saved_total_kills = self.total_kills
        saved_speed = self.player.speed_multiplier
        saved_max_health = self.player.max_health
        saved_sword_level = self.player.sword_level
        saved_has_sword = self.player.has_sword
        saved_has_bow = self.player.has_bow
        saved_has_bomb = self.player.has_bomb
        saved_extra_arrows = self.player.extra_arrows
        saved_bomb_level = self.player.bomb_level
        
        # Reset player position and health
        self.player.x = MAP_WIDTH // 2
        self.player.y = MAP_HEIGHT // 2
        self.player.health = self.player.max_health
        
        # Restore upgrades
        self.player.speed_multiplier = saved_speed
        self.player.max_health = saved_max_health
        self.player.sword_level = saved_sword_level
        self.player.has_sword = saved_has_sword
        self.player.has_bow = saved_has_bow
        self.player.has_bomb = saved_has_bomb
        self.player.extra_arrows = saved_extra_arrows
        self.player.bomb_level = saved_bomb_level
        
        # Clear enemies and arrows but keep items
        self.enemies.clear()
        self.arrows.clear()
        self.bombs.clear()
        
        # Restore wave state - go back one wave as penalty if past wave 1
        if saved_wave > 1:
            self.current_wave = saved_wave - 1
        else:
            self.current_wave = 1
        
        self.total_kills = saved_total_kills
        self.wave_active = False
        self.wave_kills = 0
        self.wave_start_time = pygame.time.get_ticks()
        
        self.game_over = False
        self.sound.play('pickup')  # Respawn sound
    
    def spawn_enemy(self) -> None:
        """Spawn enemy outside camera view."""
        # Max enemies increases with wave
        max_enemies = MAX_ENEMIES + (self.current_wave - 1) * 2
        if len([e for e in self.enemies if e.enemy_type != EnemyType.BOSS]) >= max_enemies:
            return
        
        cam_left, cam_top, cam_right, cam_bottom = self.camera.get_spawn_zone()
        side = random.randint(0, 3)
        margin = 20
        
        # Clamp spawn positions to island bounds (not in water)
        if side == 0:
            x = random.randint(max(ISLAND_LEFT, cam_left), min(ISLAND_RIGHT, cam_right))
            y = max(ISLAND_TOP, cam_top - margin)
        elif side == 1:
            x = random.randint(max(ISLAND_LEFT, cam_left), min(ISLAND_RIGHT, cam_right))
            y = min(ISLAND_BOTTOM - 20, cam_bottom + margin)
        elif side == 2:
            x = max(ISLAND_LEFT, cam_left - margin)
            y = random.randint(max(ISLAND_TOP, cam_top), min(ISLAND_BOTTOM, cam_bottom))
        else:
            x = min(ISLAND_RIGHT - 20, cam_right + margin)
            y = random.randint(max(ISLAND_TOP, cam_top), min(ISLAND_BOTTOM, cam_bottom))
        
        enemy_type = EnemyType.MONKEY if random.random() < 0.6 else EnemyType.SNAKE
        self.enemies.append(Enemy(x, y, enemy_type))
    
    def spawn_death_effect(self, enemy: Enemy, score: int) -> None:
        """Spawn death particles and floating score text."""
        cx = enemy.x + enemy.width // 2
        cy = enemy.y + enemy.height // 2
        
        # Determine colors based on enemy type
        if enemy.enemy_type == EnemyType.MONKEY:
            colors = [BROWN, (200, 150, 100), ORANGE]
            num_particles = 8
        elif enemy.enemy_type == EnemyType.SNAKE:
            colors = [GREEN, DARK_GREEN, (100, 200, 100)]
            num_particles = 10
        else:  # BOSS
            colors = [BROWN, ORANGE, (255, 200, 150), RED]
            num_particles = 20
        
        # Create explosion of death particles
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 4.0)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed - 1  # Slight upward bias
            color = random.choice(colors)
            lifetime = random.randint(20, 40)
            particle = Particle(cx, cy, color, dx, dy, lifetime)
            particle.size = random.randint(3, 6)
            self.particles.append(particle)
        
        # Create floating score text
        score_text = f"+{score}"
        self.floating_texts.append(FloatingText(cx, cy - 10, score_text, YELLOW))
    
    def spawn_tree_destruction_effect(self, tx: int, ty: int) -> None:
        """Spawn particles when a tree is destroyed by boss."""
        # Center of tree (adjust for tree visual center)
        cx = tx + 12
        cy = ty + 8
        
        # Wood and leaf colors
        colors = [BROWN, (139, 90, 43), DARK_GREEN, (34, 120, 34), (180, 140, 100)]
        
        # Create explosion of wood/leaf particles
        for _ in range(15):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.0, 5.0)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed - 2  # More upward bias
            color = random.choice(colors)
            lifetime = random.randint(25, 50)
            particle = Particle(cx, cy, color, dx, dy, lifetime)
            particle.size = random.randint(3, 7)
            self.particles.append(particle)
        
        # Add some falling leaves from top of tree
        for _ in range(6):
            leaf_x = cx + random.randint(-10, 10)
            leaf_y = ty - 6 + random.randint(-5, 5)
            dx = random.uniform(-1, 1)
            dy = random.uniform(-2, 0)
            color = random.choice([DARK_GREEN, (34, 120, 34), (60, 140, 60)])
            lifetime = random.randint(40, 60)
            particle = Particle(leaf_x, leaf_y, color, dx, dy, lifetime)
            particle.size = random.randint(2, 4)
            self.particles.append(particle)
    
    def spawn_explosion_effect(self, x: float, y: float, radius: int) -> None:
        """Spawn explosion particles for bomb."""
        colors = [RED, ORANGE, YELLOW, WHITE, (255, 100, 50)]
        
        # Main explosion ring
        num_particles = int(radius / 2) + 10
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.0, 5.0)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            color = random.choice(colors)
            lifetime = random.randint(15, 35)
            particle = Particle(x, y, color, dx, dy, lifetime)
            particle.size = random.randint(4, 8)
            self.particles.append(particle)
        
        # Inner burst
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2.0)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed - 1
            color = random.choice([WHITE, YELLOW])
            lifetime = random.randint(10, 20)
            particle = Particle(x, y, color, dx, dy, lifetime)
            particle.size = random.randint(2, 4)
            self.particles.append(particle)
    
    def spawn_wave_bosses(self) -> None:
        """Spawn bosses for the current wave."""
        if self.wave_active:
            return
        
        num_bosses = self.current_wave
        self.bosses_remaining = num_bosses
        self.loot_dropped_this_wave = False
        
        px, py = self.player.center
        
        # Spawn bosses at different positions around the island
        spawn_positions = [
            (ISLAND_RIGHT - BOSS_SIZE - 10, ISLAND_BOTTOM - BOSS_SIZE - 10),
            (ISLAND_LEFT + 10, ISLAND_TOP + 10),
            (ISLAND_RIGHT - BOSS_SIZE - 10, ISLAND_TOP + 10),
            (ISLAND_LEFT + 10, ISLAND_BOTTOM - BOSS_SIZE - 10),
            (MAP_WIDTH // 2, ISLAND_TOP + 10),
            (MAP_WIDTH // 2, ISLAND_BOTTOM - BOSS_SIZE - 10),
            (ISLAND_LEFT + 10, MAP_HEIGHT // 2),
            (ISLAND_RIGHT - BOSS_SIZE - 10, MAP_HEIGHT // 2),
        ]
        
        for i in range(num_bosses):
            pos_idx = i % len(spawn_positions)
            boss_x, boss_y = spawn_positions[pos_idx]
            # Add some randomness to position
            boss_x += random.randint(-20, 20)
            boss_y += random.randint(-20, 20)
            boss_x = max(ISLAND_LEFT, min(boss_x, ISLAND_RIGHT - BOSS_SIZE))
            boss_y = max(ISLAND_TOP, min(boss_y, ISLAND_BOTTOM - BOSS_SIZE))
            self.enemies.append(Enemy(boss_x, boss_y, EnemyType.BOSS, self.current_wave))
        
        self.wave_active = True
        if num_bosses == 1:
            self.upgrade_message = f"WAVE {self.current_wave}: BOSS SPAWNED!"
        else:
            self.upgrade_message = f"WAVE {self.current_wave}: {num_bosses} BOSSES!"
        self.upgrade_message_timer = 150
        self.sound.play('boss_spawn')
    
    def spawn_food(self) -> None:
        """Spawn random food (apples only - hearts drop from bosses, bananas from monkeys)."""
        food_count = len([i for i in self.items if i.item_type in 
                         [ItemType.APPLE, ItemType.BANANA, ItemType.DURIAN]])
        if food_count >= MAX_FOOD:
            return
        
        # Only spawn apples near trees (bananas from monkeys, hearts from bosses)
        # If no trees left, spawn at random position on island
        food_type = ItemType.APPLE
        if TREE_POSITIONS:
            tree = random.choice(TREE_POSITIONS)
            x = tree[0] + random.randint(-30, 30)
            y = tree[1] + random.randint(-30, 30)
        else:
            x = random.randint(ISLAND_LEFT + 20, ISLAND_RIGHT - 20)
            y = random.randint(ISLAND_TOP + 20, ISLAND_BOTTOM - 20)
        x = max(ISLAND_LEFT + 10, min(x, ISLAND_RIGHT - 10))
        y = max(ISLAND_TOP + 10, min(y, ISLAND_BOTTOM - 10))
        
        self.items.append(Item(x, y, food_type))
    
    def _remove_other_weapon(self, weapon_type: ItemType) -> None:
        """Remove the other weapon with a dramatic particle explosion."""
        for item in self.items[:]:
            if item.item_type == weapon_type:
                # Create explosion of particles
                cx, cy = item.x + item.width // 2, item.y + item.height // 2
                if weapon_type == ItemType.SWORD:
                    colors = [RED, ORANGE, YELLOW, WHITE]
                elif weapon_type == ItemType.BOW:
                    colors = [PURPLE, BLUE, WHITE, YELLOW]
                else:  # BOMB
                    colors = [ORANGE, RED, YELLOW, (50, 50, 50)]
                for _ in range(20):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(1, 4)
                    dx = math.cos(angle) * speed
                    dy = math.sin(angle) * speed - 2  # Upward bias
                    color = random.choice(colors)
                    lifetime = random.randint(20, 40)
                    self.particles.append(Particle(cx, cy, color, dx, dy, lifetime))
                
                self.items.remove(item)
                self.sound.play('enemy_death')  # Dramatic sound
                break
    
    def check_collisions(self) -> None:
        """Handle all collisions."""
        player_rect = self.player.rect
        
        # Item pickup
        for item in self.items[:]:
            if player_rect.colliderect(item.rect):
                if item.item_type == ItemType.SWORD:
                    self.player.has_sword = True
                    self.items.remove(item)
                    self.sound.play('sword_pickup')
                    self.upgrade_message = "SWORD CHOSEN!"
                    self.upgrade_message_timer = 90
                    # Remove other weapons dramatically
                    self._remove_other_weapon(ItemType.BOW)
                    self._remove_other_weapon(ItemType.BOMB)
                elif item.item_type == ItemType.BOW:
                    self.player.has_bow = True
                    self.items.remove(item)
                    self.sound.play('sword_pickup')
                    self.upgrade_message = "BOW CHOSEN!"
                    self.upgrade_message_timer = 90
                    # Remove other weapons dramatically
                    self._remove_other_weapon(ItemType.SWORD)
                    self._remove_other_weapon(ItemType.BOMB)
                elif item.item_type == ItemType.BOMB:
                    self.player.has_bomb = True
                    self.items.remove(item)
                    self.sound.play('sword_pickup')
                    self.upgrade_message = "BOMB CHOSEN!"
                    self.upgrade_message_timer = 90
                    # Remove other weapons dramatically
                    self._remove_other_weapon(ItemType.SWORD)
                    self._remove_other_weapon(ItemType.BOW)
                elif item.item_type in [ItemType.APPLE, ItemType.BANANA, ItemType.DURIAN]:
                    self.player.heal(item.get_heal_amount())
                    self.items.remove(item)
                    self.sound.play('pickup')
                elif item.item_type == ItemType.LOOT_BAG:
                    # Crate gives weapon upgrades based on equipped weapon
                    if self.player.has_sword:
                        upgrade = UpgradeType.IRON_SWORD
                    elif self.player.has_bow:
                        upgrade = UpgradeType.MULTI_ARROW
                    elif self.player.has_bomb:
                        upgrade = UpgradeType.MEGA_BOMB
                    else:
                        # Fallback - shouldn't happen
                        upgrade = UpgradeType.IRON_SWORD
                    
                    self.upgrade_message = self.player.apply_upgrade(upgrade)
                    self.upgrade_message_timer = 120
                    self.items.remove(item)
                    self.sound.play('upgrade')
        
        # Enemy damage to player (invincible during dodge)
        if not self.player.is_dodging:
            for enemy in self.enemies:
                if player_rect.colliderect(enemy.rect) and enemy.can_damage_player():
                    old_health = self.player.health
                    self.player.take_damage(enemy.damage)
                    if self.player.health < old_health:  # Actually took damage
                        self.camera.shake(4, 8)  # Small shake when hit
                    enemy.reset_damage_cooldown()
                    self.sound.play('hurt')
        
        # Player attack hits enemies
        attack_rect = self.player.get_attack_rect()
        if attack_rect and self.player.attack_timer == PLAYER_ATTACK_DURATION - 1:
            for enemy in self.enemies[:]:
                if attack_rect.colliderect(enemy.rect):
                    # Sword damage scales with sword_level
                    if enemy.take_damage(self.player.sword_damage):
                        if enemy.enemy_type == EnemyType.BOSS:
                            self.bosses_remaining -= 1
                            self.score += 100  # Boss kill score
                            self.spawn_death_effect(enemy, 100)
                            self.camera.shake(8, 15)  # Big shake for boss kill
                            
                            # Boss has 30% chance to drop a heart
                            if random.random() < 0.1:
                                self.items.append(Item(
                                    enemy.x + enemy.width // 2 - FOOD_SIZE // 2,
                                    enemy.y + enemy.height // 2 - FOOD_SIZE // 2,
                                    ItemType.DURIAN
                                ))
                            
                            # Only drop loot bag on last boss of the wave
                            if self.bosses_remaining <= 0 and not self.loot_dropped_this_wave:
                                self.items.append(Item(
                                    enemy.x + enemy.width // 2 - LOOT_BAG_SIZE // 2,
                                    enemy.y + enemy.height // 2 - LOOT_BAG_SIZE // 2,
                                    ItemType.LOOT_BAG
                                ))
                                self.loot_dropped_this_wave = True
                                self.upgrade_message = f"WAVE {self.current_wave} COMPLETE!"
                                self.upgrade_message_timer = 150
                                self.sound.play('wave_complete')
                                
                                # Wave complete - prepare for next wave
                                self.wave_active = False
                                self.wave_complete = True
                                self.wave_kills = 0
                                self.wave_start_time = pygame.time.get_ticks()
                                self.current_wave += 1
                            else:
                                self.upgrade_message = f"BOSS DOWN! {self.bosses_remaining} LEFT!"
                                self.upgrade_message_timer = 90
                            self.sound.play('enemy_death')
                        else:
                            # Monkey has 30% chance to drop banana
                            if enemy.enemy_type == EnemyType.MONKEY and random.random() < 0.1:
                                self.items.append(Item(
                                    enemy.x + enemy.width // 2 - 4,
                                    enemy.y + enemy.height // 2 - 4,
                                    ItemType.BANANA
                                ))
                            # Score and EXP based on enemy type
                            if enemy.enemy_type == EnemyType.MONKEY:
                                self.score += 5
                                if self.player.gain_exp(10):
                                    self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                    self.upgrade_message_timer = 90
                                self.spawn_death_effect(enemy, 5)
                            elif enemy.enemy_type == EnemyType.SNAKE:
                                self.score += 10
                                if self.player.gain_exp(20):
                                    self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                    self.upgrade_message_timer = 90
                                self.spawn_death_effect(enemy, 10)
                            self.enemies_killed += 1
                            self.total_kills += 1
                            self.wave_kills += 1
                            self.sound.play('enemy_death')
                        self.enemies.remove(enemy)
                    else:
                        self.sound.play('hit')
    
    def check_wave_trigger(self) -> None:
        """Check if next wave should spawn."""
        # Don't spawn if wave is already active
        if self.wave_active:
            return
        
        # Calculate time since wave ended (or game start for wave 1)
        elapsed_since_wave = (pygame.time.get_ticks() - self.wave_start_time) / 1000
        
        # Trigger conditions: 60 seconds OR 10 kills since last wave
        if elapsed_since_wave >= BOSS_TIME_TRIGGER or self.wave_kills >= BOSS_KILL_TRIGGER:
            self.spawn_wave_bosses()
    
    def update(self) -> None:
        """Update game state."""
        if self.game_over:
            return
        
        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update()
        
        self.camera.update(*self.player.center)
        
        for enemy in self.enemies:
            enemy.update(self.player)
            # Check if boss destroyed a tree
            if enemy.enemy_type == EnemyType.BOSS and hasattr(enemy, 'destroyed_tree_pos'):
                tx, ty = enemy.destroyed_tree_pos
                if tx >= 0:
                    self.spawn_tree_destruction_effect(tx, ty)
                    enemy.destroyed_tree_pos = (-1, -1)
        
        # Update arrows
        for arrow in self.arrows[:]:
            arrow.update()
            if not arrow.active:
                self.arrows.remove(arrow)
                continue
            # Check arrow collision with enemies
            for enemy in self.enemies[:]:
                if arrow.rect.colliderect(enemy.rect):
                    if enemy.take_damage():
                        if enemy.enemy_type == EnemyType.BOSS:
                            self.bosses_remaining -= 1
                            self.score += 100  # Boss kill score
                            self.camera.shake(8, 15)  # Big shake for boss kill
                            if self.player.gain_exp(50):  # Boss gives 50 EXP
                                self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                self.upgrade_message_timer = 90
                            self.spawn_death_effect(enemy, 100)
                            
                            # Boss has 30% chance to drop a heart
                            if random.random() < 0.1:
                                self.items.append(Item(
                                    enemy.x + enemy.width // 2 - FOOD_SIZE // 2,
                                    enemy.y + enemy.height // 2 - FOOD_SIZE // 2,
                                    ItemType.DURIAN
                                ))
                            
                            if self.bosses_remaining <= 0 and not self.loot_dropped_this_wave:
                                self.items.append(Item(
                                    enemy.x + enemy.width // 2 - LOOT_BAG_SIZE // 2,
                                    enemy.y + enemy.height // 2 - LOOT_BAG_SIZE // 2,
                                    ItemType.LOOT_BAG
                                ))
                                self.loot_dropped_this_wave = True
                                self.upgrade_message = f"WAVE {self.current_wave} COMPLETE!"
                                self.upgrade_message_timer = 150
                                self.sound.play('wave_complete')
                                self.wave_active = False
                                self.wave_complete = True
                                self.wave_kills = 0
                                self.wave_start_time = pygame.time.get_ticks()
                                self.current_wave += 1
                            else:
                                self.upgrade_message = f"BOSS DOWN! {self.bosses_remaining} LEFT!"
                                self.upgrade_message_timer = 90
                            self.sound.play('enemy_death')
                        else:
                            # Monkey has 30% chance to drop banana
                            if enemy.enemy_type == EnemyType.MONKEY and random.random() < 0.1:
                                self.items.append(Item(
                                    enemy.x + enemy.width // 2 - 4,
                                    enemy.y + enemy.height // 2 - 4,
                                    ItemType.BANANA
                                ))
                            # Score and EXP based on enemy type
                            if enemy.enemy_type == EnemyType.MONKEY:
                                self.score += 5
                                if self.player.gain_exp(10):
                                    self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                    self.upgrade_message_timer = 90
                                self.spawn_death_effect(enemy, 5)
                            elif enemy.enemy_type == EnemyType.SNAKE:
                                self.score += 10
                                if self.player.gain_exp(20):
                                    self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                    self.upgrade_message_timer = 90
                                self.spawn_death_effect(enemy, 10)
                            self.enemies_killed += 1
                            self.total_kills += 1
                            self.wave_kills += 1
                            self.sound.play('enemy_death')
                        self.enemies.remove(enemy)
                    else:
                        self.sound.play('hit')
                    arrow.active = False
                    break
        
        # Update bombs
        for bomb in self.bombs[:]:
            was_exploded = bomb.exploded
            bomb.update()
            
            # Check if bomb just exploded this frame
            if bomb.exploded and not was_exploded:
                # Create explosion effect
                self.spawn_explosion_effect(bomb.x, bomb.y, bomb.explosion_range)
                self.camera.shake(6, 12)  # Shake on explosion
                self.sound.play('enemy_death')  # Explosion sound
                
                # Damage all enemies in explosion range
                explosion_rect = bomb.get_explosion_rect()
                for enemy in self.enemies[:]:
                    # Check circular distance for more accurate explosion
                    ex, ey = enemy.center
                    dist = math.sqrt((ex - bomb.x)**2 + (ey - bomb.y)**2)
                    if dist <= bomb.explosion_range:
                        if enemy.take_damage(bomb.damage):
                            if enemy.enemy_type == EnemyType.BOSS:
                                self.bosses_remaining -= 1
                                self.score += 100
                                self.camera.shake(8, 15)
                                if self.player.gain_exp(50):
                                    self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                    self.upgrade_message_timer = 90
                                self.spawn_death_effect(enemy, 100)
                                
                                if random.random() < 0.3:
                                    self.items.append(Item(
                                        enemy.x + enemy.width // 2 - FOOD_SIZE // 2,
                                        enemy.y + enemy.height // 2 - FOOD_SIZE // 2,
                                        ItemType.DURIAN
                                    ))
                                
                                if self.bosses_remaining <= 0 and not self.loot_dropped_this_wave:
                                    self.items.append(Item(
                                        enemy.x + enemy.width // 2 - LOOT_BAG_SIZE // 2,
                                        enemy.y + enemy.height // 2 - LOOT_BAG_SIZE // 2,
                                        ItemType.LOOT_BAG
                                    ))
                                    self.loot_dropped_this_wave = True
                                    self.upgrade_message = f"WAVE {self.current_wave} COMPLETE!"
                                    self.upgrade_message_timer = 150
                                    self.sound.play('wave_complete')
                                    self.wave_active = False
                                    self.wave_complete = True
                                    self.wave_kills = 0
                                    self.wave_start_time = pygame.time.get_ticks()
                                    self.current_wave += 1
                                else:
                                    self.upgrade_message = f"BOSS DOWN! {self.bosses_remaining} LEFT!"
                                    self.upgrade_message_timer = 90
                                self.sound.play('enemy_death')
                            else:
                                if enemy.enemy_type == EnemyType.MONKEY and random.random() < 0.3:
                                    self.items.append(Item(
                                        enemy.x + enemy.width // 2 - 4,
                                        enemy.y + enemy.height // 2 - 4,
                                        ItemType.BANANA
                                    ))
                                if enemy.enemy_type == EnemyType.MONKEY:
                                    self.score += 5
                                    if self.player.gain_exp(10):
                                        self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                        self.upgrade_message_timer = 90
                                    self.spawn_death_effect(enemy, 5)
                                elif enemy.enemy_type == EnemyType.SNAKE:
                                    self.score += 10
                                    if self.player.gain_exp(20):
                                        self.upgrade_message = f"LEVEL UP! LV {self.player.level}"
                                        self.upgrade_message_timer = 90
                                    self.spawn_death_effect(enemy, 10)
                                self.enemies_killed += 1
                                self.total_kills += 1
                                self.wave_kills += 1
                                self.sound.play('enemy_death')
                            self.enemies.remove(enemy)
                
                # Remove bomb after explosion
                self.bombs.remove(bomb)
        
        # Enemy spawn interval decreases with each wave (faster spawns)
        spawn_interval = max(800, ENEMY_SPAWN_INTERVAL - (self.current_wave - 1) * 300)
        if current_time - self.last_enemy_spawn >= spawn_interval:
            self.spawn_enemy()
            self.last_enemy_spawn = current_time
        
        if current_time - self.last_food_spawn >= FOOD_SPAWN_INTERVAL:
            self.spawn_food()
            self.last_food_spawn = current_time
        
        # Update particles
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)
        
        # Update floating texts
        for text in self.floating_texts[:]:
            if not text.update():
                self.floating_texts.remove(text)
        
        self.check_collisions()
        self.check_wave_trigger()
        
        if self.upgrade_message_timer > 0:
            self.upgrade_message_timer -= 1
        
        if self.player.health <= 0 and not self.game_over:
            self.game_over = True
            self.final_time = (pygame.time.get_ticks() - self.start_time) // 1000
            self.sound.play('game_over')
            # Save high score with weapon info
            if not self.score_saved and self.score > 0:
                weapon = "Sword" if self.player.has_sword else "Bow" if self.player.has_bow else "None"
                self.last_rank = self.add_high_score(self.score, self.final_time, self.current_wave, weapon)
                self.score_saved = True
    
    def draw_map(self) -> None:
        """Draw the hellish lava map."""
        # Animated lava background
        self.game_surface.fill(LAVA_DARK)
        
        # Draw lava flow animation
        time = pygame.time.get_ticks()
        for lx in range(-50, INTERNAL_WIDTH + 50, 30):
            for ly in range(-50, INTERNAL_HEIGHT + 50, 30):
                # Offset based on world position for consistency
                world_x = lx + self.camera.x
                world_y = ly + self.camera.y
                # Only draw in lava areas (outside island)
                island_x = world_x - ISLAND_LEFT
                island_y = world_y - ISLAND_TOP
                if (island_x < -10 or island_x > ISLAND_RIGHT - ISLAND_LEFT + 10 or
                    island_y < -10 or island_y > ISLAND_BOTTOM - ISLAND_TOP + 10):
                    # Animated lava bubbles
                    phase = (time // 100 + int(world_x * 0.1) + int(world_y * 0.1)) % 20
                    if phase < 3:
                        bubble_color = LAVA_BRIGHT if phase < 1 else LAVA
                        pygame.draw.circle(self.game_surface, bubble_color, (lx + phase * 2, ly), 4 + phase)
        
        # Draw some lava streaks
        for i in range(5):
            streak_phase = (time // 50 + i * 40) % 200
            streak_y = (i * 80 + streak_phase) % INTERNAL_HEIGHT
            streak_x = (i * 100) % INTERNAL_WIDTH
            if streak_phase < 100:
                pygame.draw.ellipse(self.game_surface, LAVA, (streak_x - 20, streak_y, 40, 8))
        
        # Hell platform (irregular rocky surface)
        # Transform world coordinates to screen coordinates
        if PLATFORM_EDGE_POINTS:
            # Outer rocky edge
            screen_outer = [(int(x - self.camera.x), int(y - self.camera.y)) 
                           for x, y in PLATFORM_EDGE_POINTS]
            pygame.draw.polygon(self.game_surface, ROCK_DARK, screen_outer)
            
            # Inner platform surface
            screen_inner = [(int(x - self.camera.x), int(y - self.camera.y)) 
                           for x, y in PLATFORM_INNER_POINTS]
            pygame.draw.polygon(self.game_surface, ROCK, screen_inner)
            
            # Glowing lava edge around platform
            pygame.draw.polygon(self.game_surface, LAVA, screen_outer, width=2)
            
            # Add some rocky texture/cracks on the surface
            for i in range(0, len(PLATFORM_INNER_POINTS), 4):
                p1 = PLATFORM_INNER_POINTS[i]
                p2 = PLATFORM_INNER_POINTS[(i + len(PLATFORM_INNER_POINTS) // 2) % len(PLATFORM_INNER_POINTS)]
                # Only draw partial cracks
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2
                sx1, sy1 = int(p1[0] - self.camera.x), int(p1[1] - self.camera.y)
                smx, smy = int(mid_x - self.camera.x), int(mid_y - self.camera.y)
                pygame.draw.line(self.game_surface, ROCK_DARK, (sx1, sy1), (smx, smy), 1)
        
        # Dead/burnt trees
        for tx, ty in TREE_POSITIONS:
            screen_x, screen_y = self.camera.apply_pos(tx, ty)
            sx, sy = int(screen_x), int(screen_y)
            # Charred tree trunk
            pygame.draw.rect(self.game_surface, DEAD_TREE_DARK, (sx + 8, sy + 8, 8, 14))
            # Dead branches (no foliage, just twisted branches)
            pygame.draw.line(self.game_surface, DEAD_TREE, (sx + 12, sy + 8), (sx + 4, sy - 2), 2)
            pygame.draw.line(self.game_surface, DEAD_TREE, (sx + 12, sy + 8), (sx + 20, sy - 4), 2)
            pygame.draw.line(self.game_surface, DEAD_TREE, (sx + 12, sy + 4), (sx + 12, sy - 6), 2)
            pygame.draw.line(self.game_surface, DEAD_TREE_DARK, (sx + 12, sy - 6), (sx + 8, sy - 10), 2)
            pygame.draw.line(self.game_surface, DEAD_TREE_DARK, (sx + 12, sy - 6), (sx + 16, sy - 10), 2)
            # Ember glow at base
            if (time // 300 + tx) % 3 == 0:
                pygame.draw.circle(self.game_surface, LAVA_BRIGHT, (sx + 12, sy + 20), 3)
    
    def draw_ui(self) -> None:
        """Draw HUD on game surface."""
        # Bar settings - longer and thinner
        bar_x, bar_y = 6, 4
        bar_width, bar_height = 140, 7
        
        # HP bar on top
        pygame.draw.rect(self.game_surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        health_ratio = self.player.health / self.player.max_health
        health_color = GREEN if health_ratio > 0.5 else YELLOW if health_ratio > 0.25 else RED
        pygame.draw.rect(self.game_surface, health_color, 
                        (bar_x, bar_y, int(bar_width * health_ratio), bar_height))
        pygame.draw.rect(self.game_surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
        hp_text = f"HP {self.player.health}/{self.player.max_health}"
        self._draw_text(hp_text, bar_x + bar_width + 5, bar_y - 1, WHITE)
        
        # EXP bar below HP bar
        exp_bar_y = bar_y + bar_height + 3
        pygame.draw.rect(self.game_surface, (40, 40, 40), (bar_x, exp_bar_y, bar_width, bar_height))
        exp_ratio = self.player.exp / self.player.exp_per_level
        pygame.draw.rect(self.game_surface, (100, 200, 255), 
                        (bar_x, exp_bar_y, int(bar_width * exp_ratio), bar_height))
        pygame.draw.rect(self.game_surface, WHITE, (bar_x, exp_bar_y, bar_width, bar_height), 1)
        exp_text = f"LV{self.player.level} {self.player.exp}/{self.player.exp_per_level}"
        self._draw_text(exp_text, bar_x + bar_width + 5, exp_bar_y - 1, (100, 200, 255))
        
        # Stats below bars - spaced out properly
        stats_y = exp_bar_y + bar_height + 6
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        self._draw_text(f"Time: {elapsed}s", bar_x, stats_y, WHITE)
        self._draw_text(f"Kills: {self.total_kills}", bar_x + 70, stats_y, WHITE)
        
        # Wave and weapon info
        info_y = stats_y + 14
        self._draw_text(f"Wave: {self.current_wave}", bar_x, info_y, PURPLE)
        
        # Weapon indicator on same line
        if not self.player.has_sword and not self.player.has_bow and not self.player.has_bomb:
            self._draw_text("Pick weapon!", bar_x + 60, info_y, YELLOW)
        elif self.player.has_sword:
            sword_txt = f"Sword+{self.player.sword_level}" if self.player.sword_level > 0 else "Sword"
            self._draw_text(sword_txt, bar_x + 60, info_y, GREEN)
        elif self.player.has_bow:
            arrows_txt = f"Bow+{self.player.extra_arrows}" if self.player.extra_arrows > 0 else "Bow"
            self._draw_text(arrows_txt, bar_x + 60, info_y, GREEN)
        elif self.player.has_bomb:
            bomb_txt = f"Bomb+{self.player.bomb_level}" if self.player.bomb_level > 0 else "Bomb"
            self._draw_text(bomb_txt, bar_x + 60, info_y, ORANGE)
        
        # Wave/Boss status
        status_y = info_y + 14
        if self.wave_active:
            if self.bosses_remaining > 0:
                self._draw_text(f"Bosses: {self.bosses_remaining}", bar_x, status_y, RED)
        else:
            elapsed_since_wave = (pygame.time.get_ticks() - self.wave_start_time) // 1000
            time_to_wave = max(0, BOSS_TIME_TRIGGER - elapsed_since_wave)
            kills_to_wave = max(0, BOSS_KILL_TRIGGER - self.wave_kills)
            self._draw_text(f"Next: {time_to_wave}s / {kills_to_wave}kills", bar_x, status_y, ORANGE)
        
        # Score display on top right
        score_text = f"Score: {self.score}"
        score_surface = self.font.render(score_text, False, YELLOW)
        score_x = INTERNAL_WIDTH - score_surface.get_width() - 8
        shadow_surface = self.font.render(score_text, False, BLACK)
        self.game_surface.blit(shadow_surface, (score_x + 1, bar_y + 1))
        self.game_surface.blit(score_surface, (score_x, bar_y))
        
        # Upgrade message
        if self.upgrade_message_timer > 0:
            self._draw_text_centered(self.upgrade_message, INTERNAL_HEIGHT // 4, YELLOW, big=True, alpha=180)
        
        # Game over
        if self.game_over:
            overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            self.game_surface.blit(overlay, (0, 0))
            
            # Title
            self._draw_text_centered("GAME OVER", 30, RED, big=True)
            
            # Current run stats (use saved final_time)
            weapon_name = "Sword" if self.player.has_sword else "Bow" if self.player.has_bow else "None"
            self._draw_text_centered(f"Score: {self.score}  Time: {self.final_time}s  Wave: {self.current_wave}  [{weapon_name}]", 65, YELLOW)
            
            # Show rank if made it to top 10
            if self.last_rank > 0:
                self._draw_text_centered(f"NEW HIGH SCORE! Rank #{self.last_rank}", 85, GREEN)
            
            # High scores header
            self._draw_text_centered("= TOP 10 HIGH SCORES =", 110, WHITE)
            
            # Display high scores
            y_start = 130
            for i, hs in enumerate(self.high_scores[:10]):
                rank = i + 1
                weapon = hs.get('weapon', '?')
                weapon_icon = "⚔" if weapon == "Sword" else "🏹" if weapon == "Bow" else "?"
                score_text = f"{rank}. {hs['score']}pts  {hs['time']}s  W{hs['wave']}  [{weapon}]"
                # Highlight current score
                if rank == self.last_rank:
                    color = GREEN
                else:
                    color = (200, 200, 200) if rank <= 3 else (150, 150, 150)
                self._draw_text_centered(score_text, y_start + i * 16, color)
            
            # Fill empty slots
            for i in range(len(self.high_scores), 10):
                rank = i + 1
                self._draw_text_centered(f"{rank}. ---", y_start + i * 16, (80, 80, 80))
            
            # Controls
            self._draw_text_centered("Press R to Restart", INTERNAL_HEIGHT - 25, WHITE)
    
    def _draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int], alpha: int = 180) -> None:
        """Draw text with shadow at position, semi-transparent."""
        shadow = self.font.render(text, False, (0, 0, 0))
        surface = self.font.render(text, False, color)
        shadow.set_alpha(alpha // 2)
        surface.set_alpha(alpha)
        self.game_surface.blit(shadow, (x + 1, y + 1))
        self.game_surface.blit(surface, (x, y))
    
    def _draw_text_centered(self, text: str, y: int, color: Tuple[int, int, int], big: bool = False, alpha: int = 255) -> None:
        """Draw centered text with shadow."""
        font = self.big_font if big else self.font
        shadow = font.render(text, False, (0, 0, 0))
        surface = font.render(text, False, color)
        if alpha < 255:
            shadow.set_alpha(alpha // 2)
            surface.set_alpha(alpha)
        rect = surface.get_rect(center=(INTERNAL_WIDTH // 2, y))
        self.game_surface.blit(shadow, (rect.x + 2, rect.y + 2))
        self.game_surface.blit(surface, rect)
    
    def draw_instructions(self) -> None:
        """Draw the instruction screen."""
        self.game_surface.fill((30, 15, 15))  # Dark red background
        
        # Title
        self._draw_text_centered("HELL SURVIVOR", 40, LAVA_BRIGHT, big=True)
        
        # Author credit
        self._draw_text_centered("Author: Haoran Liu, 2025", 75, (150, 150, 150))
        
        # Subtitle
        self._draw_text_centered("How to Play", 100, WHITE)
        
        # Controls section
        y = 125
        controls = [
            ("WASD / Arrow Keys", "Move"),
            ("SPACE", "Attack / Shoot"),
            ("SHIFT", "Dodge Roll"),
            ("F11", "Toggle Fullscreen"),
            ("R", "Restart (when dead)"),
        ]
        
        for key, action in controls:
            self._draw_text(key, 120, y, YELLOW)
            self._draw_text(action, 300, y, WHITE)
            y += 18
        
        # Game tips
        y += 15
        self._draw_text_centered("--- Tips ---", y, (150, 200, 255))
        y += 20
        tips = [
            "Pick up a weapon to start!",
            "Kill enemies to trigger boss waves",
            "Defeat bosses for upgrades & hearts"
        ]
        for tip in tips:
            self._draw_text_centered(tip, y, (180, 180, 180))
            y += 16
        
        # Start prompt (flashing)
        if (self.frame_count // 30) % 2 == 0:
            self._draw_text_centered("Press SPACE to Start", INTERNAL_HEIGHT - 30, WHITE)
    
    def draw(self) -> None:
        """Render everything with retro scaling and CRT effect."""
        # Show instructions screen if active
        if self.show_instructions:
            self.draw_instructions()
            # Scale up and apply CRT
            scaled = pygame.transform.scale(self.game_surface, (self.window_width, self.window_height))
            self.screen.blit(scaled, (0, 0))
            self.crt_filter.apply(self.screen)
            pygame.display.flip()
            return
        
        # Draw to internal low-res surface
        self.draw_map()
        
        for item in self.items:
            item.draw(self.game_surface, self.camera, self.frame_count)
        
        for arrow in self.arrows:
            arrow.draw(self.game_surface, self.camera)
        
        for bomb in self.bombs:
            bomb.draw(self.game_surface, self.camera)
        
        for enemy in self.enemies:
            enemy.draw(self.game_surface, self.camera)
        
        self.player.draw(self.game_surface, self.camera)
        
        # Draw particles on top
        for particle in self.particles:
            particle.draw(self.game_surface, self.camera)
        
        # Draw floating score texts
        for text in self.floating_texts:
            text.draw(self.game_surface, self.camera, self.font)
        
        self.draw_ui()
        
        # Scale up to window size (nearest neighbor for crisp pixels)
        scaled = pygame.transform.scale(self.game_surface, (self.window_width, self.window_height))
        self.screen.blit(scaled, (0, 0))
        
        # Apply CRT filter
        self.crt_filter.apply(self.screen)
        
        pygame.display.flip()
    
    def handle_events(self) -> None:
        """Process events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                if not self.is_fullscreen:
                    self.handle_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.show_instructions:
                        self.show_instructions = False
                        self.start_time = pygame.time.get_ticks()  # Reset timer
                    elif self.player.has_bow and self.player.shoot():
                        # Shoot arrows based on direction and upgrades
                        cx, cy = self.player.center
                        for dx, dy in self.player.get_arrow_directions():
                            self.arrows.append(Arrow(cx, cy, dx, dy))
                        self.sound.play('attack')
                    elif self.player.has_bomb and self.player.throw_bomb():
                        # Throw bomb in facing direction
                        cx, cy = self.player.center
                        if self.player.direction == Direction.UP:
                            dx, dy = 0, -1
                        elif self.player.direction == Direction.DOWN:
                            dx, dy = 0, 1
                        elif self.player.direction == Direction.LEFT:
                            dx, dy = -1, 0
                        else:
                            dx, dy = 1, 0
                        self.bombs.append(Bomb(cx, cy, dx, dy, self.player.bomb_damage, self.player.bomb_range))
                        self.sound.play('attack')
                    elif self.player.attack():
                        self.sound.play('attack')
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if not self.game_over and self.player.dodge():
                        self.sound.play('dodge')
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    if self.is_fullscreen:
                        self.toggle_fullscreen()
                    else:
                        self.running = False
    
    async def run(self) -> None:
        """Main game loop."""
        while self.running:
            self.frame_count += 1
            self.handle_events()
            if not self.show_instructions:
                self.update()
            self.draw()
            self.clock.tick(FPS)
            await asyncio.sleep(0)  # Yield control to browser
        
        pygame.quit()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Entry point."""
    game = GameManager()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
