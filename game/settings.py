from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAVE_PATH = BASE_DIR.parent / "savegame.json"
USERS_DB_PATH = BASE_DIR.parent / "users.db"
SAVES_DIR = BASE_DIR.parent / "saves"
LOGS_DIR = BASE_DIR.parent / "logs"

WINDOW_TITLE = "RuneScape Valley Prototype"
WINDOW_SIZE = (1280, 720)

TILE_SIZE = 1.0
WORLD_WIDTH = 30
WORLD_HEIGHT = 30

PLAYER_SPEED = 4.0
INTERACTION_RANGE = 1

CAMERA_PAN_SPEED = 14.0
CAMERA_ROTATE_SPEED = 80.0
CAMERA_ZOOM_STEP = 2.0
CAMERA_MIN_ZOOM = 8.0
CAMERA_MAX_ZOOM = 34.0
CAMERA_PITCH_DEGREES = 55.0

START_DAY = 1
START_MINUTE = 6 * 60
GAME_MINUTES_PER_REAL_SECOND = 8.0
