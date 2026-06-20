from __future__ import annotations

import unittest

from game.world.grid import TileGrid
from game.world.map import WorldMap
from game.world.pathfinding import find_path


class PathfindingTests(unittest.TestCase):
    def test_finds_open_diagonal_path(self) -> None:
        grid = TileGrid(5, 5)

        path = find_path(grid, (0, 0), (2, 2), set())

        self.assertEqual(path, [(0, 0), (1, 1), (2, 2)])

    def test_diagonal_does_not_clip_past_one_blocked_corner(self) -> None:
        grid = TileGrid(3, 3)

        path = find_path(grid, (0, 0), (1, 1), {(1, 0)})

        self.assertEqual(path, [(0, 0), (0, 1), (1, 1)])

    def test_diagonal_does_not_clip_past_two_blocked_corners(self) -> None:
        grid = TileGrid(3, 3)

        path = find_path(grid, (0, 0), (1, 1), {(1, 0), (0, 1)})

        self.assertIsNone(path)

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

    def test_world_water_tiles_are_blocked(self) -> None:
        world = WorldMap(
            {
                "width": 3,
                "height": 3,
                "water_tiles": [[1, 0]],
                "blocked_tiles": [],
                "resource_nodes": [],
            }
        )

        self.assertIn((1, 0), world.blocked_tiles())

    def test_no_path_when_destination_is_water(self) -> None:
        grid = TileGrid(3, 3)

        path = find_path(grid, (0, 0), (1, 0), {(1, 0)})

        self.assertIsNone(path)

    def test_path_routes_around_water(self) -> None:
        grid = TileGrid(4, 3)
        water = {(1, 0)}

        path = find_path(grid, (0, 0), (3, 0), water)

        self.assertIsNotNone(path)
        assert path is not None
        self.assertTrue(all(tile not in water for tile in path))
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (3, 0))


if __name__ == "__main__":
    unittest.main()
