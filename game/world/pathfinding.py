from __future__ import annotations

import heapq
from typing import Iterable

from game.world.grid import Tile, TileGrid


def find_path(
    grid: TileGrid,
    start: Tile,
    goal: Tile,
    blocked_tiles: Iterable[Tile],
) -> list[Tile] | None:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return None

    blocked = set(blocked_tiles)
    blocked.discard(start)
    if goal in blocked:
        return None

    frontier: list[tuple[int, Tile]] = []
    heapq.heappush(frontier, (0, start))
    came_from: dict[Tile, Tile | None] = {start: None}
    cost_so_far: dict[Tile, int] = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break

        for neighbor in grid.neighbors(current):
            if neighbor in blocked:
                continue
            new_cost = cost_so_far[current] + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + _manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

    if goal not in came_from:
        return None

    path: list[Tile] = []
    current: Tile | None = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


def _manhattan(a: Tile, b: Tile) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
