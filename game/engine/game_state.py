from __future__ import annotations

from enum import Enum


class GameState(str, Enum):
    LOGIN = "login"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"
    ERROR = "error"
