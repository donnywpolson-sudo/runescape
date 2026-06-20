from __future__ import annotations

from types import SimpleNamespace

from game.systems.gathering import GatheringSystem, ResourceNode
from game.systems.interaction import InteractionManager
from game.systems.inventory import Inventory
from game.systems.shop import Shop
from game.systems.skills import Skills
from game.world.grid import TileGrid
from game.world.objects import WorldObject


def test_diagonal_adjacency_counts_for_shop_interaction() -> None:
    feedback: list[str] = []
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        Inventory(),
        Skills(),
        Shop({"logs": {"sell_price": 3}}),
        lambda amount: None,
        feedback.append,
    )

    manager.interact_with(WorldObject("shop_01", "shop", (1, 1)))

    assert feedback == ["No sellable items"]


def test_bank_interaction_opens_bank_callback() -> None:
    opened: list[bool] = []
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        Inventory(),
        Skills(),
        Shop({"logs": {"sell_price": 3}}),
        lambda amount: None,
        lambda message: None,
        open_bank=lambda: opened.append(True),
    )

    manager.interact_with(WorldObject("bank_01", "bank", (1, 1)))

    assert opened == [True]


def test_move_cancels_pending_gathering() -> None:
    grid = TileGrid(4, 4)
    gathering = GatheringSystem([_tree()], Inventory(), Skills(_skills()), time_provider=lambda: 100.0)
    gathering.start_gather("tree_01", (1, 2), grid, gathering.blocking_tiles())
    player = _Player(tile=(1, 2))
    manager = InteractionManager(
        SimpleNamespace(grid=grid, blocked_tiles=lambda: set()),
        player,
        gathering.inventory,
        gathering.skills,
        Shop({"logs": {"sell_price": 3}}),
        lambda amount: None,
        lambda message: None,
        gathering,
    )

    manager.move_to_tile((0, 0))

    assert gathering.pending is None
    assert player.path


def _skills() -> dict[str, dict[str, object]]:
    return {
        "woodcutting": {
            "display_name": "Woodcutting",
            "starting_level": 1,
            "xp_thresholds": {"1": 0, "2": 100},
        }
    }


def _tree() -> ResourceNode:
    return ResourceNode(
        node_id="tree_01",
        node_type="tree",
        display_name="Tree",
        skill_id="woodcutting",
        required_level=1,
        xp_reward=25,
        item_reward="logs",
        quantity_reward=1,
        depleted_state="stump",
        respawn_seconds=30,
        base_gather_seconds=2.0,
        blocks_movement=True,
        position=(2, 2),
    )


class _Player:
    def __init__(self, tile: tuple[int, int]) -> None:
        self.tile = tile
        self.path: list[tuple[int, int]] = []

    @property
    def is_moving(self) -> bool:
        return bool(self.path)

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = path
