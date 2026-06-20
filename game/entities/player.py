from __future__ import annotations

import math

from panda3d.core import NodePath, Vec3

from game import settings
from game.world.grid import Tile, TileGrid
from game.world.objects import make_box, make_cone, make_cylinder

TUNIC = (0.22, 0.38, 0.62, 1.0)
SLEEVE = (0.16, 0.24, 0.38, 1.0)
TROUSERS = (0.24, 0.18, 0.14, 1.0)
SKIN = (0.88, 0.67, 0.46, 1.0)
HAIR = (0.24, 0.13, 0.05, 1.0)


class Player:
    def __init__(self, grid: TileGrid, start_tile: Tile) -> None:
        self.grid = grid
        self.tile = start_tile
        self.x, self.y = grid.to_world(start_tile)
        self.path: list[Tile] = []
        self.node: NodePath | None = None
        self.heading = 0.0

    def render(self, parent: NodePath) -> None:
        self.node = parent.attachNewNode("player")

        left_leg = make_box("player_left_leg", (0.11, 0.12, 0.34), TROUSERS)
        left_leg.reparentTo(self.node)
        left_leg.setPos(-0.08, 0.0, 0.02)

        right_leg = make_box("player_right_leg", (0.11, 0.12, 0.34), TROUSERS)
        right_leg.reparentTo(self.node)
        right_leg.setPos(0.08, 0.0, 0.02)

        body = make_box("player_body", (0.34, 0.24, 0.44), TUNIC)
        body.reparentTo(self.node)
        body.setZ(0.34)

        left_arm = make_box("player_left_arm", (0.09, 0.10, 0.34), SLEEVE)
        left_arm.reparentTo(self.node)
        left_arm.setPos(-0.25, 0.0, 0.38)

        right_arm = make_box("player_right_arm", (0.09, 0.10, 0.34), SLEEVE)
        right_arm.reparentTo(self.node)
        right_arm.setPos(0.25, 0.0, 0.38)

        head = make_cylinder("player_head", 0.16, 0.20, 8, SKIN)
        head.reparentTo(self.node)
        head.setZ(0.80)

        hair = make_cone("player_hair", 0.17, 0.12, 8, HAIR)
        hair.reparentTo(self.node)
        hair.setZ(0.99)

        self._sync_node()

    @property
    def is_moving(self) -> bool:
        return bool(self.path)

    def set_path(self, path: list[Tile]) -> None:
        self.path = list(path)
        if self.path and self.path[0] == self.tile:
            self.path.pop(0)

    def update(self, dt: float) -> None:
        if not self.path:
            return

        target_tile = self.path[0]
        target_x, target_y = self.grid.to_world(target_tile)
        dx = target_x - self.x
        dy = target_y - self.y
        distance = (dx * dx + dy * dy) ** 0.5
        step = settings.PLAYER_SPEED * dt

        if distance <= step or distance < 0.001:
            self.x = target_x
            self.y = target_y
            self.tile = target_tile
            self.path.pop(0)
        else:
            self.heading = math.degrees(math.atan2(-dx, dy))
            self.x += dx / distance * step
            self.y += dy / distance * step

        self._sync_node()

    def set_position_tile(self, tile: Tile) -> None:
        self.tile = tile
        self.x, self.y = self.grid.to_world(tile)
        self.path.clear()
        self._sync_node()

    def to_dict(self) -> dict[str, object]:
        return {"tile": list(self.tile), "position": [self.x, self.y]}

    def load_dict(self, data: dict[str, object]) -> None:
        tile_data = data.get("tile", self.tile)
        tile = (int(tile_data[0]), int(tile_data[1]))  # type: ignore[index]
        if self.grid.in_bounds(tile):
            self.tile = tile
            self.x, self.y = self.grid.to_world(tile)

        position = data.get("position")
        if isinstance(position, list) and len(position) == 2:
            self.x = float(position[0])
            self.y = float(position[1])
        self.path.clear()
        self._sync_node()

    def _sync_node(self) -> None:
        if self.node is not None:
            self.node.setPos(Vec3(self.x, self.y, 0.02))
            self.node.setH(self.heading)
