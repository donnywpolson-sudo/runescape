from __future__ import annotations

import heapq
from typing import Iterable, Iterator

from game.world.grid import Tile, TileGrid

CARDINAL_COST = 10
DIAGONAL_COST = 14


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

        for neighbor in _walkable_neighbors(grid, current, blocked):
            new_cost = cost_so_far[current] + _movement_cost(current, neighbor)
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + _octile(neighbor, goal)
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


def _walkable_neighbors(
    grid: TileGrid,
    tile: Tile,
    blocked: set[Tile],
) -> Iterator[Tile]:
    for neighbor in grid.neighbors(tile, diagonals=True):
        if neighbor in blocked:
            continue
        if _is_diagonal(tile, neighbor) and not _can_move_diagonal(tile, neighbor, grid, blocked):
            continue
        yield neighbor


def _can_move_diagonal(
    start: Tile,
    end: Tile,
    grid: TileGrid,
    blocked: set[Tile],
) -> bool:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    side_x = (start[0] + dx, start[1])
    side_y = (start[0], start[1] + dy)
    return (
        grid.in_bounds(side_x)
        and grid.in_bounds(side_y)
        and side_x not in blocked
        and side_y not in blocked
    )


def _movement_cost(a: Tile, b: Tile) -> int:
    return DIAGONAL_COST if _is_diagonal(a, b) else CARDINAL_COST


def _is_diagonal(a: Tile, b: Tile) -> bool:
    return a[0] != b[0] and a[1] != b[1]


def _octile(a: Tile, b: Tile) -> int:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    diagonal_steps = min(dx, dy)
    cardinal_steps = max(dx, dy) - diagonal_steps
    return DIAGONAL_COST * diagonal_steps + CARDINAL_COST * cardinal_steps
