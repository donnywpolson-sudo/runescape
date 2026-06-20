from __future__ import annotations

import math

from panda3d.core import NodePath, Vec3

from game import settings
from game.world import visuals
from game.world.grid import Tile, TileGrid


class Player:
    def __init__(self, grid: TileGrid, start_tile: Tile) -> None:
        self.grid = grid
        self.tile = start_tile
        self.x, self.y = grid.to_world(start_tile)
        self.path: list[Tile] = []
        self.node: NodePath | None = None
        self.parts: dict[str, NodePath] = {}
        self.heading = 0.0
        self.walk_time = 0.0
        self.action_animation: str | None = None
        self.action_time = 0.0

    def render(self, parent: NodePath) -> None:
        self.node = parent.attachNewNode("player")
        self.parts = visuals.render_player_model(self.node)
        self._sync_node()

    @property
    def is_moving(self) -> bool:
        return bool(self.path)

    def set_path(self, path: list[Tile]) -> None:
        self.path = list(path)
        if self.path and self.path[0] == self.tile:
            self.path.pop(0)
        if self.path:
            self.stop_action_animation(sync=False)

    def update(self, dt: float) -> None:
        if not self.path:
            self.walk_time = 0.0
            if self.action_animation is not None:
                self.action_time += dt
            self._sync_node()
            return

        self.stop_action_animation(sync=False)
        self.walk_time += dt * 9.0
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
        self.stop_action_animation(sync=False)
        self.tile = tile
        self.x, self.y = self.grid.to_world(tile)
        self.path.clear()
        self._sync_node()

    def to_dict(self) -> dict[str, object]:
        return {"tile": list(self.tile), "position": [self.x, self.y]}

    def load_dict(self, data: dict[str, object]) -> None:
        self.stop_action_animation(sync=False)
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

    def start_action_animation(self, action_type: str) -> None:
        if self.action_animation != action_type:
            self.action_time = 0.0
        self.action_animation = action_type
        self._sync_node()

    def stop_action_animation(self, *, sync: bool = True) -> bool:
        if self.action_animation is None and self.action_time == 0.0:
            return False
        self.action_animation = None
        self.action_time = 0.0
        if sync:
            self._sync_node()
        return True

    def _sync_node(self) -> None:
        if self.node is not None:
            bob = 0.0
            if self.path:
                bob = abs(math.sin(self.walk_time)) * 0.035
                sway = math.sin(self.walk_time) * 6.0
                self._set_part_hpr("left_leg", 0.0, sway, 0.0)
                self._set_part_hpr("right_leg", 0.0, -sway, 0.0)
                self._set_part_hpr("left_arm", 0.0, -sway * 0.6, 0.0)
                self._set_part_hpr("right_arm", 0.0, sway * 0.6, 0.0)
                self._reset_upper_pose()
            else:
                self._reset_pose()
                if self.action_animation is not None:
                    self._apply_action_pose(self.action_animation)
            self.node.setPos(Vec3(self.x, self.y, 0.02 + bob))
            self.node.setH(self.heading)

    def _apply_action_pose(self, action_type: str) -> None:
        cycle = math.sin(self.action_time * 6.0)
        if action_type == "woodcutting":
            self._set_part_hpr("body", 0.0, 0.0, -3.0)
            self._set_part_hpr("right_arm", 0.0, -24.0 + cycle * 9.0, 7.0)
            self._set_part_hpr("left_arm", 0.0, 8.0, -5.0)
            self._set_part_hpr("tool", -24.0, -18.0 + cycle * 12.0, -18.0)
        elif action_type == "mining":
            self._set_part_hpr("body", 0.0, 2.0, 2.0)
            self._set_part_hpr("right_arm", 0.0, -30.0 + cycle * 10.0, 4.0)
            self._set_part_hpr("left_arm", 0.0, 6.0, -4.0)
            self._set_part_hpr("tool", -12.0, -24.0 + cycle * 14.0, -8.0)
        elif action_type == "fishing":
            self._set_part_hpr("body", 0.0, 4.0 + cycle * 1.5, -2.0)
            self._set_part_hpr("right_arm", 0.0, -14.0, -24.0 + cycle * 5.0)
            self._set_part_hpr("left_arm", 0.0, 8.0, 10.0)
            self._set_part_hpr("tool", -34.0, 2.0, -38.0 + cycle * 8.0)
        elif action_type == "cooking":
            self._set_part_hpr("body", 0.0, 3.0 + cycle * 1.0, 1.5)
            self._set_part_hpr("right_arm", 0.0, -12.0 + cycle * 6.0, 12.0)
            self._set_part_hpr("left_arm", 0.0, 9.0, -8.0)
            self._set_part_hpr("tool", -8.0, -8.0 + cycle * 6.0, 18.0)
        elif action_type == "smelting":
            self._set_part_hpr("body", 0.0, 4.0 + cycle * 0.8, 0.0)
            self._set_part_hpr("right_arm", 0.0, -8.0, 8.0)
            self._set_part_hpr("left_arm", 0.0, 6.0, -8.0)
        elif action_type == "smithing":
            self._set_part_hpr("body", 0.0, 2.0, 2.0)
            self._set_part_hpr("right_arm", 0.0, -32.0 + cycle * 12.0, 6.0)
            self._set_part_hpr("left_arm", 0.0, 10.0, -5.0)
            self._set_part_hpr("tool", -10.0, -26.0 + cycle * 16.0, -6.0)
        elif action_type == "combat":
            self._set_part_hpr("body", 0.0, 1.5, 4.0 + cycle * 2.0)
            self._set_part_hpr("right_arm", 0.0, -24.0 + cycle * 8.0, 16.0)
            self._set_part_hpr("left_arm", 0.0, 12.0, -14.0)
            self._set_part_hpr("tool", -18.0, -18.0 + cycle * 10.0, 12.0)

    def _reset_pose(self) -> None:
        for key in ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head"):
            self._set_part_hpr(key, 0.0, 0.0, 0.0)
        self._set_part_hpr("tool", -16.0, 0.0, -10.0)

    def _reset_upper_pose(self) -> None:
        for key in ("body", "head"):
            self._set_part_hpr(key, 0.0, 0.0, 0.0)
        self._set_part_hpr("tool", -16.0, 0.0, -10.0)

    def _set_part_hpr(self, key: str, h: float, p: float, r: float) -> None:
        part = self.parts.get(key)
        if part is None:
            return
        part.setHpr(h, p, r)
