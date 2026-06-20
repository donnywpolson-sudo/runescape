from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from game.engine.save import load_game, save_game
from game.systems.gathering import GatheringSystem, ResourceNode
from game.systems.inventory import Inventory
from game.systems.skills import Skills
from game.world.grid import TileGrid


SKILLS = {
    "woodcutting": {
        "display_name": "Woodcutting",
        "starting_level": 1,
        "xp_thresholds": {"1": 0, "2": 100},
    },
    "mining": {
        "display_name": "Mining",
        "starting_level": 1,
        "xp_thresholds": {"1": 0, "2": 100},
    },
    "fishing": {
        "display_name": "Fishing",
        "starting_level": 1,
        "xp_thresholds": {"1": 0, "2": 100},
    },
}


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class GatheringTests(unittest.TestCase):
    def test_gathering_grants_correct_item_and_skill_xp(self) -> None:
        system, inventory, skills, grid = _system([_tree()])

        result = system.gather("tree_01", (1, 2), grid, system.blocking_tiles())

        self.assertTrue(result.success)
        self.assertEqual(inventory.count("logs"), 1)
        self.assertEqual(skills.xp("woodcutting"), 25)
        self.assertEqual(result.feedback, "Chopped tree: +1 logs, +25 Woodcutting XP")

    def test_required_level_blocks_gathering(self) -> None:
        rock = _rock(required_level=2)
        system, inventory, skills, grid = _system([rock])

        result = system.gather("copper_rock_01", (1, 2), grid, system.blocking_tiles())

        self.assertFalse(result.success)
        self.assertEqual(result.feedback, "You need Mining level 2")
        self.assertEqual(inventory.count("copper_ore"), 0)
        self.assertEqual(skills.xp("mining"), 0)

    def test_depleted_node_cannot_be_gathered_until_respawn(self) -> None:
        clock = FakeClock()
        system, inventory, skills, grid = _system([_tree(respawn_seconds=10)], clock=clock)

        self.assertTrue(system.gather("tree_01", (1, 2), grid, system.blocking_tiles()).success)
        self.assertFalse(system.gather("tree_01", (1, 2), grid, system.blocking_tiles()).success)

        clock.now = 109.0
        self.assertFalse(system.gather("tree_01", (1, 2), grid, system.blocking_tiles()).success)

        clock.now = 110.0
        self.assertTrue(system.gather("tree_01", (1, 2), grid, system.blocking_tiles()).success)
        self.assertEqual(inventory.count("logs"), 2)
        self.assertEqual(skills.xp("woodcutting"), 50)

    def test_all_three_skills_use_same_gathering_system(self) -> None:
        nodes = [_tree(), _rock(), _fish()]
        system, inventory, skills, grid = _system(nodes)

        results = [
            system.gather("tree_01", (1, 2), grid, system.blocking_tiles()),
            system.gather("copper_rock_01", (1, 3), grid, system.blocking_tiles()),
            system.gather("fishing_spot_01", (4, 4), grid, system.blocking_tiles()),
        ]

        self.assertTrue(all(result.success for result in results))
        self.assertIsInstance(system, GatheringSystem)
        self.assertEqual(inventory.count("logs"), 1)
        self.assertEqual(inventory.count("copper_ore"), 1)
        self.assertEqual(inventory.count("raw_fish"), 1)
        self.assertEqual(skills.xp("woodcutting"), 25)
        self.assertEqual(skills.xp("mining"), 20)
        self.assertEqual(skills.xp("fishing"), 15)

    def test_gathering_walks_to_reachable_adjacent_tile(self) -> None:
        system, _, _, grid = _system([_tree()])

        result = system.gather("tree_01", (0, 0), grid, system.blocking_tiles())

        self.assertTrue(result.success)
        self.assertIn(result.new_player_tile, {(1, 2), (2, 1), (2, 3), (3, 2)})

    def test_save_load_preserves_inventory_skills_and_depleted_nodes(self) -> None:
        clock = FakeClock()
        system, inventory, skills, grid = _system([_tree(respawn_seconds=30)], clock=clock)
        system.gather("tree_01", (1, 2), grid, system.blocking_tiles())
        state = {
            "inventory": inventory.to_dict(),
            "skills": skills.to_dict(),
            "world": {"resource_nodes": system.to_dict()},
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            save_game(path, state)
            loaded = load_game(path)

        assert loaded is not None
        loaded_inventory = Inventory.from_dict(loaded["inventory"])
        loaded_skills = Skills(SKILLS)
        loaded_skills.load_dict(loaded["skills"])
        loaded_system = GatheringSystem([_tree(respawn_seconds=30)], loaded_inventory, loaded_skills, time_provider=clock)
        loaded_system.load_dict(loaded["world"]["resource_nodes"])

        self.assertEqual(loaded_inventory.count("logs"), 1)
        self.assertEqual(loaded_skills.xp("woodcutting"), 25)
        self.assertTrue(loaded_system.is_depleted("tree_01"))


def _system(
    nodes: list[ResourceNode],
    *,
    clock: FakeClock | None = None,
) -> tuple[GatheringSystem, Inventory, Skills, TileGrid]:
    inventory = Inventory()
    skills = Skills(SKILLS)
    grid = TileGrid(6, 6)
    system = GatheringSystem(nodes, inventory, skills, time_provider=clock or FakeClock())
    return system, inventory, skills, grid


def _tree(respawn_seconds: float = 30) -> ResourceNode:
    return ResourceNode(
        node_id="tree_01",
        node_type="tree",
        skill_id="woodcutting",
        required_level=1,
        xp_reward=25,
        item_reward="logs",
        quantity_reward=1,
        depleted_state="stump",
        respawn_seconds=respawn_seconds,
        blocks_movement=True,
        position=(2, 2),
    )


def _rock(required_level: int = 1) -> ResourceNode:
    return ResourceNode(
        node_id="copper_rock_01",
        node_type="copper_rock",
        skill_id="mining",
        required_level=required_level,
        xp_reward=20,
        item_reward="copper_ore",
        quantity_reward=1,
        depleted_state="depleted_rock",
        respawn_seconds=30,
        blocks_movement=True,
        position=(2, 3),
    )


def _fish() -> ResourceNode:
    return ResourceNode(
        node_id="fishing_spot_01",
        node_type="fishing_spot",
        skill_id="fishing",
        required_level=1,
        xp_reward=15,
        item_reward="raw_fish",
        quantity_reward=1,
        depleted_state="quiet_water",
        respawn_seconds=30,
        blocks_movement=False,
        position=(4, 4),
    )


if __name__ == "__main__":
    unittest.main()
