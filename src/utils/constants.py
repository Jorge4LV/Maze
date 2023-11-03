"""
Contains constants, not secrets but things that might change.
"""

# Colors
COLOR_BLURPLE = 0x7289DA
COLOR_GREEN = 0x2ECC71
COLOR_ORANGE = 0xE67E22
COLOR_RED = 0xE74C3C

# Maze stuff
MAX_LEVELS = 10 # can go up to 25 but bigger mazes take longer to generate, so max is level 10, 25x25, 85s time limit
MAX_PLAYERS = 5 # max 5 people per lobby, can go higher but breaks embed if it's too big and can be rate limited on race start
TIME_LIMIT_BASE = 1 # level 1-5 = 60 seconds, which is between 7x7 and 15x15 since size is (level + 2) and * 2 + 1 (after mazelib)
TIME_LIMIT_THRESHOLD = 5 # after level 5 it adds 5 extra seconds per level = base + (level - threshold) * 5
IMAGE_SIZE = 1024 # size of maze images in pixels