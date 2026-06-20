from __future__ import annotations

from typing import Optional

from panda3d.core import Point3

from game.world.grid import Tile, TileGrid


def ground_point_from_mouse(base) -> Optional[Point3]:
    if not base.mouseWatcherNode.hasMouse():
        return None

    mouse_pos = base.mouseWatcherNode.getMouse()
    near = Point3()
    far = Point3()
    base.camLens.extrude(mouse_pos, near, far)

    near_world = base.render.getRelativePoint(base.camera, near)
    far_world = base.render.getRelativePoint(base.camera, far)
    ray = far_world - near_world

    # Intersect the mouse ray with the z=0 ground plane.
    if abs(ray.z) < 0.0001:
        return None

    t = -near_world.z / ray.z
    if t < 0:
        return None
    return near_world + ray * t


def ground_tile_from_mouse(base, grid: TileGrid) -> tuple[Optional[Tile], Optional[Point3]]:
    point = ground_point_from_mouse(base)
    if point is None:
        return None, None
    return grid.from_world(point.x, point.y), point


def object_from_mouse(base, world_map) -> object | None:
    tile, _ = ground_tile_from_mouse(base, world_map.grid)
    if tile is None:
        return None
    return world_map.object_at(tile)
