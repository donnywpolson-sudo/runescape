from __future__ import annotations

from dataclasses import dataclass

from game.world.grid import Tile


@dataclass(frozen=True)
class Npc:
    npc_id: str
    name: str
    tile: Tile
