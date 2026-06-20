from __future__ import annotations

from dataclasses import dataclass

from game import settings

Tile = tuple[int, int]


@dataclass(frozen=True)
class TileGrid:
    width: int
    height: int

    def in_bounds(self, tile: Tile) -> bool:
        x, y = tile
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbors(self, tile: Tile, *, diagonals: bool = False) -> list[Tile]:
        x, y = tile
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if diagonals:
            candidates.extend(
                [
                    (x + 1, y + 1),
                    (x + 1, y - 1),
                    (x - 1, y + 1),
                    (x - 1, y - 1),
                ]
            )
        return [candidate for candidate in candidates if self.in_bounds(candidate)]

    def to_world(self, tile: Tile) -> tuple[float, float]:
        x, y = tile
        return (
            (x + 0.5) * settings.TILE_SIZE,
            (y + 0.5) * settings.TILE_SIZE,
        )

    def from_world(self, x: float, y: float) -> Tile | None:
        tile = (int(x // settings.TILE_SIZE), int(y // settings.TILE_SIZE))
        if not self.in_bounds(tile):
            return None
        return tile
