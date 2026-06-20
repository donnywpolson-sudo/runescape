from __future__ import annotations

from types import SimpleNamespace

from game.systems.combat import CombatSystem
from game.systems.cooking import CookingSystem
from game.systems.gathering import GatheringSystem, ResourceNode
from game.systems.interaction import InteractionManager
from game.systems.inventory import Inventory
from game.systems.shop import Shop
from game.systems.skills import Skills, osrs_xp_thresholds
from game.world.grid import TileGrid
from game.world.map import WorldMap
from game.world.objects import WorldObject


def test_diagonal_adjacency_counts_for_shop_interaction() -> None:
    opened: list[bool] = []
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        Inventory(),
        Skills(),
        Shop({"logs": {"sell_price": 3}}),
        lambda amount: None,
        lambda message: None,
        open_shop=lambda: opened.append(True),
    )

    manager.interact_with(WorldObject("shop_01", "shop", (1, 1)))

    assert opened == [True]


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


def test_shop_interaction_opens_shop_without_autoselling() -> None:
    inventory = Inventory({"logs": 2})
    opened: list[bool] = []
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        inventory,
        Skills(),
        Shop({"logs": {"sell_price": 3}, "coins": {"sell_price": 0}}),
        lambda amount: inventory.add("coins", amount),
        lambda message: None,
        open_shop=lambda: opened.append(True),
    )

    manager.interact_with(WorldObject("shop_01", "shop", (1, 1)))

    assert inventory.to_dict() == {"logs": 2}
    assert opened == [True]


def test_context_action_generation_covers_interactable_types() -> None:
    world = WorldMap(
        {
            "width": 6,
            "height": 6,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [_tree().to_dict()],
            "furnace": {"id": "furnace_01", "tile": [3, 1]},
            "anvil": {"id": "anvil_01", "tile": [4, 1]},
            "npcs": [{"id": "guide_01", "name": "Village Guide", "tile": [1, 3], "quest_id": "starter_path"}],
            "mobs": [_mob_data()],
        }
    )
    inventory = Inventory({"bronze_axe": 1})
    skills = Skills(_skills())
    manager = InteractionManager(
        world,
        _Player(tile=(1, 1)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        lambda message: None,
        gathering=GatheringSystem([_tree()], inventory, skills),
        combat=CombatSystem(world.mob_definitions),
    )

    assert _action_ids(manager, "tree_01") == ["gather", "examine", "cancel"]
    assert manager.get_actions(world.get_object("tree_01"))[0].label == "Chop down Tree"
    assert _action_ids(manager, "furnace_01") == ["smelt", "examine", "cancel"]
    assert _action_ids(manager, "anvil_01") == ["smith", "examine", "cancel"]
    assert _action_ids(manager, "guide_01") == ["talk", "examine", "cancel"]
    assert _action_ids(manager, "mob_01") == ["attack", "examine", "cancel"]


def test_perform_action_separates_examine_from_npc_talk() -> None:
    feedback: list[str] = []
    talked_to: list[str] = []
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        Inventory(),
        Skills(),
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        talk_to_npc=lambda obj: talked_to.append(obj.object_id),
    )
    npc = WorldObject("guide_01", "npc", (1, 1), display_name="Village Guide")

    manager.perform_action("examine", npc)
    manager.perform_action("talk", npc)

    assert feedback == ["Village Guide"]
    assert talked_to == ["guide_01"]


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


def test_cooking_range_requires_selected_raw_fish() -> None:
    feedback: list[str] = []
    inventory = Inventory({"raw_shrimp": 1})
    skills = Skills(_skills())
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        cooking=CookingSystem(_items(), inventory, skills),
    )

    manager.interact_with(WorldObject("cooking_range_01", "cooking_range", (1, 1)))

    assert feedback == ["Select a raw fish first"]


def test_selecting_raw_fish_then_range_starts_cooking() -> None:
    feedback: list[str] = []
    inventory = Inventory({"raw_shrimp": 1})
    skills = Skills(_skills())
    cooking = CookingSystem(_items(), inventory, skills, time_provider=lambda: 100.0)
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        cooking=cooking,
    )

    manager.select_inventory_item("raw_shrimp")
    manager.interact_with(WorldObject("cooking_range_01", "cooking_range", (1, 1)))

    assert manager.selected_item_id == "raw_shrimp"
    assert cooking.pending is not None
    assert feedback[-2:] == ["Selected item: Raw shrimp", "Cooking Raw shrimp... 1.8s"]


def test_move_cancels_pending_cooking() -> None:
    grid = TileGrid(4, 4)
    inventory = Inventory({"raw_shrimp": 1})
    skills = Skills(_skills())
    cooking = CookingSystem(_items(), inventory, skills, time_provider=lambda: 100.0)
    cooking.start_cooking("raw_shrimp")
    player = _Player(tile=(1, 2))
    manager = InteractionManager(
        SimpleNamespace(grid=grid, blocked_tiles=lambda: set()),
        player,
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        lambda message: None,
        cooking=cooking,
    )

    manager.move_to_tile((0, 0))

    assert cooking.pending is None
    assert player.path


def test_combat_walks_adjacent_kills_mob_and_spawns_pickup_drop() -> None:
    clock = FakeClock()
    world = WorldMap(
        {
            "width": 5,
            "height": 5,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [],
            "mobs": [_mob_data()],
        }
    )
    inventory = Inventory()
    combat = CombatSystem(world.mob_definitions, time_provider=clock)
    player = _Player(tile=(0, 0))
    feedback: list[str] = []
    manager = InteractionManager(
        world,
        player,
        inventory,
        Skills(_skills()),
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        combat=combat,
    )

    manager.interact_with(world.get_object("mob_01"))

    assert player.path
    assert manager.pending_object_id == "mob_01"

    player.tile = player.path[-1]
    player.path.clear()
    manager.update()

    assert combat.pending is not None
    assert feedback[-1] == "Attacking Worn dummy... 1.0s"

    clock.now += 1.0
    manager.update()
    clock.now += 1.0
    manager.update()

    assert world.get_object("mob_01").active is False
    ground_items = [obj for obj in world.objects.values() if obj.kind == "ground_item"]
    assert [obj.item_id for obj in ground_items] == ["coins", "wooden_splinters"]
    assert feedback[-1] == "Defeated Worn dummy; drops appeared"

    manager.interact_with(ground_items[0])

    assert inventory.count("coins") == 3
    assert world.get_object(ground_items[0].object_id) is None


def _skills() -> dict[str, dict[str, object]]:
    return {
        "woodcutting": {
            "display_name": "Woodcutting",
            "starting_level": 1,
            "xp_thresholds": osrs_xp_thresholds(),
        },
        "cooking": {
            "display_name": "Cooking",
            "starting_level": 1,
            "xp_thresholds": osrs_xp_thresholds(),
        },
    }


def _items() -> dict[str, dict[str, object]]:
    return {
        "logs": {"name": "Logs", "category": "wood", "sell_price": 3},
        "raw_shrimp": {
            "name": "Raw shrimp",
            "category": "fish",
            "sell_price": 4,
            "cook_result": "cooked_shrimp",
            "cooking_required_level": 1,
            "cooking_xp": 30,
            "base_cook_seconds": 1.8,
        },
        "cooked_shrimp": {"name": "Cooked shrimp", "category": "fish", "sell_price": 7},
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


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def _mob_data() -> dict[str, object]:
    return {
        "mob_id": "mob_01",
        "display_name": "Worn dummy",
        "level": 1,
        "hitpoints": 2,
        "attack_seconds": 1.0,
        "respawn_seconds": 5.0,
        "position": [2, 2],
        "drops": [
            {"item_id": "coins", "quantity": 3},
            {"item_id": "wooden_splinters", "quantity": 1},
        ],
    }


def _action_ids(manager: InteractionManager, object_id: str) -> list[str]:
    return [action.action_id for action in manager.get_actions(manager.world_map.get_object(object_id))]
