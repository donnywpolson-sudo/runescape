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
        "xp_thresholds": {"1": 0, "2": 100, "3": 250},
    },
    "mining": {
        "display_name": "Mining",
        "starting_level": 1,
        "xp_thresholds": {"1": 0, "2": 100, "3": 250},
    },
    "fishing": {
        "display_name": "Fishing",
        "starting_level": 1,
        "xp_thresholds": {"1": 0, "2": 100, "3": 250},
    },
}


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class GatheringTests(unittest.TestCase):
    def test_gathering_completes_after_timer_and_grants_rewards(self) -> None:
        system, inventory, skills, grid, clock = _system([_tree()])

        started = system.start_gather("tree_01", (1, 2), grid, system.blocking_tiles())

        self.assertTrue(started.success)
        self.assertTrue(started.pending)
        self.assertEqual(started.feedback, "Chopping Tree... 2.0s")
        self.assertEqual(inventory.count("logs"), 0)
        self.assertIsNone(system.update())

        clock.now += 2.0
        completed = system.update()

        assert completed is not None
        self.assertTrue(completed.success)
        self.assertEqual(inventory.count("logs"), 1)
        self.assertEqual(skills.xp("woodcutting"), 25)
        self.assertEqual(completed.feedback, "Chopped Tree: +1 logs, +25 Woodcutting XP")

    def test_diagonal_adjacency_can_start_gathering(self) -> None:
        system, _, _, grid, _ = _system([_tree()])

        result = system.start_gather("tree_01", (1, 1), grid, system.blocking_tiles())

        self.assertTrue(result.success)
        self.assertTrue(result.pending)
        self.assertEqual(result.new_player_tile, None)

    def test_required_level_blocks_each_skill(self) -> None:
        for node, start_tile, feedback in [
            (_tree(required_level=2), (1, 2), "You need Woodcutting level 2"),
            (_rock(required_level=2), (1, 3), "You need Mining level 2"),
            (_fish(required_level=2), (4, 4), "You need Fishing level 2"),
        ]:
            system, inventory, skills, grid, _ = _system([node])

            result = system.start_gather(node.node_id, start_tile, grid, system.blocking_tiles())

            self.assertFalse(result.success)
            self.assertEqual(result.feedback, feedback)
            self.assertEqual(inventory.to_dict(), {})
            self.assertEqual(skills.xp(node.skill_id), 0)

    def test_depleted_node_cannot_be_gathered_until_respawn(self) -> None:
        system, inventory, skills, grid, clock = _system([_tree(respawn_seconds=10)])

        self._start_and_finish(system, "tree_01", (1, 2), grid, clock)
        self.assertFalse(system.start_gather("tree_01", (1, 2), grid, system.blocking_tiles()).success)

        clock.now = 111.0
        self.assertFalse(system.start_gather("tree_01", (1, 2), grid, system.blocking_tiles()).success)

        clock.now = 112.0
        self._start_and_finish(system, "tree_01", (1, 2), grid, clock)
        self.assertEqual(inventory.count("logs"), 2)
        self.assertEqual(skills.xp("woodcutting"), 50)

    def test_all_three_skills_use_same_gathering_system(self) -> None:
        nodes = [_tree(), _rock(), _fish()]
        system, inventory, skills, grid, clock = _system(nodes)

        self._start_and_finish(system, "tree_01", (1, 2), grid, clock)
        self._start_and_finish(system, "copper_rock_01", (1, 3), grid, clock)
        self._start_and_finish(system, "shrimp_spot_01", (4, 4), grid, clock)

        self.assertIsInstance(system, GatheringSystem)
        self.assertEqual(inventory.count("logs"), 1)
        self.assertEqual(inventory.count("copper_ore"), 1)
        self.assertEqual(inventory.count("raw_shrimp"), 1)
        self.assertEqual(skills.xp("woodcutting"), 25)
        self.assertEqual(skills.xp("mining"), 20)
        self.assertEqual(skills.xp("fishing"), 15)

    def test_gathering_walks_to_reachable_adjacent_tile_before_starting(self) -> None:
        system, inventory, _, grid, _ = _system([_tree()])

        result = system.start_gather("tree_01", (0, 0), grid, system.blocking_tiles())

        self.assertTrue(result.success)
        self.assertFalse(result.pending)
        self.assertEqual(result.new_player_tile, (1, 1))
        self.assertEqual(inventory.count("logs"), 0)

    def test_higher_level_reduces_gather_duration(self) -> None:
        system, _, skills, _, _ = _system([_tree()])
        node = system.nodes["tree_01"]

        level_one_duration = system.gather_duration(node)
        skills.add_xp("woodcutting", 250)
        level_three_duration = system.gather_duration(node)

        self.assertEqual(level_one_duration, 2.0)
        self.assertEqual(level_three_duration, 1.6)

    def test_pending_gathering_can_be_cancelled(self) -> None:
        system, inventory, _, grid, clock = _system([_tree()])

        system.start_gather("tree_01", (1, 2), grid, system.blocking_tiles())
        self.assertTrue(system.cancel_pending())
        clock.now += 2.0

        self.assertIsNone(system.update())
        self.assertEqual(inventory.count("logs"), 0)

    def test_save_load_preserves_inventory_skills_and_depleted_nodes(self) -> None:
        system, inventory, skills, grid, clock = _system([_tree(respawn_seconds=30)])
        self._start_and_finish(system, "tree_01", (1, 2), grid, clock)
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

    def _start_and_finish(
        self,
        system: GatheringSystem,
        node_id: str,
        player_tile: tuple[int, int],
        grid: TileGrid,
        clock: FakeClock,
    ) -> None:
        started = system.start_gather(node_id, player_tile, grid, system.blocking_tiles())
        self.assertTrue(started.success)
        self.assertTrue(started.pending)
        clock.now += started.duration
        completed = system.update()
        assert completed is not None
        self.assertTrue(completed.success)


def _system(
    nodes: list[ResourceNode],
    *,
    clock: FakeClock | None = None,
) -> tuple[GatheringSystem, Inventory, Skills, TileGrid, FakeClock]:
    inventory = Inventory()
    skills = Skills(SKILLS)
    grid = TileGrid(6, 6)
    clock = clock or FakeClock()
    system = GatheringSystem(nodes, inventory, skills, time_provider=clock)
    return system, inventory, skills, grid, clock


def _tree(required_level: int = 1, respawn_seconds: float = 30) -> ResourceNode:
    return ResourceNode(
        node_id="tree_01",
        node_type="tree",
        display_name="Tree",
        skill_id="woodcutting",
        required_level=required_level,
        xp_reward=25,
        item_reward="logs",
        quantity_reward=1,
        depleted_state="stump",
        respawn_seconds=respawn_seconds,
        base_gather_seconds=2.0,
        blocks_movement=True,
        position=(2, 2),
    )


def _rock(required_level: int = 1) -> ResourceNode:
    return ResourceNode(
        node_id="copper_rock_01",
        node_type="copper_rock",
        display_name="Copper rock",
        skill_id="mining",
        required_level=required_level,
        xp_reward=20,
        item_reward="copper_ore",
        quantity_reward=1,
        depleted_state="depleted_rock",
        respawn_seconds=30,
        base_gather_seconds=2.2,
        blocks_movement=True,
        position=(2, 3),
    )


def _fish(required_level: int = 1) -> ResourceNode:
    return ResourceNode(
        node_id="shrimp_spot_01",
        node_type="shrimp_spot",
        display_name="Raw shrimp",
        skill_id="fishing",
        required_level=required_level,
        xp_reward=15,
        item_reward="raw_shrimp",
        quantity_reward=1,
        depleted_state="quiet_water",
        respawn_seconds=30,
        base_gather_seconds=1.8,
        blocks_movement=False,
        position=(4, 4),
    )


if __name__ == "__main__":
    unittest.main()
