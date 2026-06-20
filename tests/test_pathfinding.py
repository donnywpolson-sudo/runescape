from __future__ import annotations

import unittest

from game.world.grid import TileGrid
from game.world.pathfinding import find_path


class PathfindingTests(unittest.TestCase):
    def test_finds_path_around_blocked_tiles(self) -> None:
        grid = TileGrid(5, 5)
        blocked = {(1, 0), (1, 1), (1, 2), (1, 3)}

        path = find_path(grid, (0, 0), (4, 0), blocked)

        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (4, 0))
        self.assertTrue(all(tile not in blocked for tile in path))

    def test_no_path_when_destination_enclosed(self) -> None:
        grid = TileGrid(5, 5)
        blocked = {(2, 1), (1, 2), (3, 2), (2, 3)}

        path = find_path(grid, (0, 0), (2, 2), blocked)

        self.assertIsNone(path)

    def test_no_path_when_destination_blocked(self) -> None:
        grid = TileGrid(5, 5)

        path = find_path(grid, (0, 0), (2, 2), {(2, 2)})

        self.assertIsNone(path)

    def test_no_path_when_destination_out_of_bounds(self) -> None:
        grid = TileGrid(5, 5)

        path = find_path(grid, (0, 0), (9, 9), set())

        self.assertIsNone(path)


if __name__ == "__main__":
    unittest.main()
