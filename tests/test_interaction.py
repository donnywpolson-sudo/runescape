from __future__ import annotations

from types import SimpleNamespace

from game.systems.combat import CombatSystem
from game.systems.cooking import CookingSystem
from game.systems.gathering import GatheringSystem, ResourceNode
from game.systems.interaction import InteractionManager
from game.systems.inventory import Inventory
from game.systems.shop import Shop
from game.systems.skills import Skills, skill_xp_thresholds
from game.systems.smithing import SmithingSystem
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
            "combat_dummy": {"id": "combat_dummy_01", "name": "Training dummy", "tile": [5, 1]},
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
        train_combat=lambda: None,
    )

    assert _action_ids(manager, "tree_01") == ["gather", "examine", "cancel"]
    assert manager.get_actions(world.get_object("tree_01"))[0].label == "Chop down Tree"
    assert _action_ids(manager, "furnace_01") == ["smelt", "examine", "cancel"]
    assert _action_ids(manager, "anvil_01") == ["smith", "examine", "cancel"]
    assert _action_ids(manager, "guide_01") == ["talk", "examine", "cancel"]
    assert _action_ids(manager, "mob_01") == ["attack", "examine", "cancel"]
    assert _action_ids(manager, "combat_dummy_01") == ["train", "examine", "cancel"]


def test_fishing_spot_actions_and_feedback_show_requirements_and_catch() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [[1, 1]],
            "resource_nodes": [
                {
                    "node_id": "shrimp_spot_01",
                    "node_type": "shrimp_spot",
                    "display_name": "Fishing spot",
                    "skill_id": "fishing",
                    "required_level": 1,
                    "xp_reward": 15,
                    "item_reward": "raw_shrimp",
                    "quantity_reward": 1,
                    "depleted_state": "quiet_water",
                    "respawn_seconds": 15,
                    "base_gather_seconds": 1.8,
                    "blocks_movement": False,
                    "position": [1, 1],
                }
            ],
        }
    )
    inventory = Inventory({"fishing_rod": 1})
    skills = Skills(_skills())
    feedback: list[str] = []
    gathering = GatheringSystem(world.resource_nodes, inventory, skills, time_provider=lambda: 100.0, item_definitions=_items())
    manager = InteractionManager(
        world,
        _Player(tile=(1, 2)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        gathering=gathering,
    )
    spot = world.get_object("shrimp_spot_01")

    assert manager.get_actions(spot)[0].label == "Fish Fishing spot"

    manager.perform_action("examine", spot)
    manager.interact_with(spot)

    assert feedback[-2] == "Fishing spot: requires Fishing level 1 and fishing rod; yields Raw shrimp"
    assert feedback[-1] == "Fishing Fishing spot... 1.8s; requires Fishing level 1 and fishing rod; catches Raw shrimp"


def test_training_dummy_uses_train_callback() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "combat_dummy": {"id": "combat_dummy_01", "name": "Training dummy", "tile": [1, 1]},
        }
    )
    trained: list[bool] = []
    manager = InteractionManager(
        world,
        _Player(tile=(1, 2)),
        Inventory(),
        Skills(_skills()),
        Shop(_items()),
        lambda amount: None,
        lambda message: None,
        train_combat=lambda: trained.append(True),
    )

    manager.interact_with(world.get_object("combat_dummy_01"))

    assert trained == [True]


def test_ground_item_actions_and_default_pickup() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [],
        }
    )
    ground_item = world.add_ground_item("coins", 3, (1, 1))
    inventory = Inventory()
    feedback: list[str] = []
    manager = InteractionManager(
        world,
        _Player(tile=(1, 1)),
        inventory,
        Skills(_skills()),
        Shop(_items()),
        lambda amount: None,
        feedback.append,
    )

    assert manager.get_actions(ground_item)[0].action_id == "take"
    assert manager.get_actions(ground_item)[0].label == "Take Coins"

    manager.interact_with(ground_item)

    assert inventory.count("coins") == 3
    assert world.get_object(ground_item.object_id) is None
    assert feedback[-1] == "Picked up 3 Coins"


def test_ground_item_pickup_is_blocked_when_inventory_is_full() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [],
        }
    )
    ground_item = world.add_ground_item("raw_shrimp", 1, (1, 1))
    inventory = Inventory({"logs": 28})
    feedback: list[str] = []
    manager = InteractionManager(
        world,
        _Player(tile=(1, 1)),
        inventory,
        Skills(_skills()),
        Shop(_items()),
        lambda amount: None,
        feedback.append,
    )

    manager.interact_with(ground_item)

    assert inventory.to_dict() == {"logs": 28}
    assert world.get_object(ground_item.object_id) is ground_item
    assert feedback[-1] == "Inventory is full"


def test_left_click_ground_item_uses_pickup_interaction(monkeypatch) -> None:
    from game.engine import app as app_module

    ground_item = WorldObject("ground_item_0001", "ground_item", (2, 2), blocking=False, item_id="coins", quantity=3)
    interactions = _ClickInteractions()
    hidden: list[bool] = []
    shown: list[tuple[object, tuple[int, int]]] = []
    fake_app = SimpleNamespace(
        hud=SimpleNamespace(hide_context_menu=lambda: hidden.append(True)),
        world_map=SimpleNamespace(grid=object()),
        destination_marker=object(),
        interactions=interactions,
        selected_text="",
        _show_marker=lambda marker, tile: shown.append((marker, tile)),
        set_feedback=lambda message: None,
    )
    monkeypatch.setattr(app_module, "target_from_mouse", lambda _base, _world_map: ground_item)
    monkeypatch.setattr(app_module, "ground_tile_from_mouse", lambda _base, _grid: ((3, 3), None))

    app_module.GameApp.on_left_click(fake_app)

    assert hidden == [True]
    assert shown == [(fake_app.destination_marker, (2, 2))]
    assert interactions.interacted == [ground_item]
    assert interactions.moved == []


def test_left_click_gameplay_object_uses_default_interaction(monkeypatch) -> None:
    from game.engine import app as app_module

    tree = WorldObject("tree_01", "tree", (2, 2), display_name="Tree")
    interactions = _ClickInteractions()
    shown: list[tuple[object, tuple[int, int]]] = []
    fake_app = SimpleNamespace(
        hud=SimpleNamespace(hide_context_menu=lambda: None),
        world_map=SimpleNamespace(grid=object()),
        destination_marker=object(),
        interactions=interactions,
        selected_text="",
        _show_marker=lambda marker, tile: shown.append((marker, tile)),
        set_feedback=lambda message: None,
    )
    monkeypatch.setattr(app_module, "target_from_mouse", lambda _base, _world_map: tree)
    monkeypatch.setattr(app_module, "ground_tile_from_mouse", lambda _base, _grid: ((3, 3), None))

    app_module.GameApp.on_left_click(fake_app)

    assert shown == [(fake_app.destination_marker, (2, 2))]
    assert interactions.interacted == [tree]
    assert interactions.moved == []


def test_left_click_over_hud_does_not_pick_world_or_move(monkeypatch) -> None:
    from game.engine import app as app_module

    interactions = _ClickInteractions()
    fake_app = SimpleNamespace(
        hud=SimpleNamespace(pointer_over_blocking_ui=lambda _pos: True, hide_context_menu=lambda: None),
        interactions=interactions,
    )
    monkeypatch.setattr(app_module, "target_from_mouse", lambda _base, _world_map: (_ for _ in ()).throw(AssertionError("picked world")))
    monkeypatch.setattr(app_module, "ground_tile_from_mouse", lambda _base, _grid: (_ for _ in ()).throw(AssertionError("picked ground")))

    app_module.GameApp.on_left_click(fake_app)

    assert interactions.interacted == []
    assert interactions.moved == []


def test_right_click_ground_opens_walk_here_menu(monkeypatch) -> None:
    from game.engine import app as app_module

    menu_calls: list[tuple[list[tuple[str, str]], tuple[float, float, float]]] = []
    moved: list[tuple[int, int]] = []
    fake_app = SimpleNamespace(
        hud=SimpleNamespace(
            show_context_menu=lambda actions, _command, pos: menu_calls.append((actions, pos)),
        ),
        world_map=SimpleNamespace(grid=object()),
        selection_marker=object(),
        interactions=SimpleNamespace(move_to_tile=moved.append),
        selected_text="",
        _show_marker=lambda marker, tile: None,
        _context_menu_pos=lambda: (0.25, 0, 0.30),
        set_feedback=lambda message: None,
    )
    monkeypatch.setattr(app_module, "target_from_mouse", lambda _base, _world_map: None)
    monkeypatch.setattr(app_module, "ground_tile_from_mouse", lambda _base, _grid: ((3, 3), None))

    app_module.GameApp.on_right_click(fake_app)

    assert menu_calls == [([("walk", "Walk here"), ("cancel", "Cancel")], (0.25, 0, 0.30))]
    assert moved == []


def test_right_click_over_hud_does_not_open_world_context(monkeypatch) -> None:
    from game.engine import app as app_module

    fake_app = SimpleNamespace(
        hud=SimpleNamespace(pointer_over_blocking_ui=lambda _pos: True),
    )
    monkeypatch.setattr(app_module, "target_from_mouse", lambda _base, _world_map: (_ for _ in ()).throw(AssertionError("picked world")))

    app_module.GameApp.on_right_click(fake_app)


def test_scenery_actions_walk_and_examine() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [],
            "decorations": [
                {"id": "sign_01", "kind": "signpost", "position": [2, 2]},
            ],
        }
    )
    player = _Player(tile=(0, 0))
    feedback: list[str] = []
    manager = InteractionManager(
        world,
        player,
        Inventory(),
        Skills(_skills()),
        Shop(_items()),
        lambda amount: None,
        feedback.append,
    )
    scenery = world.target_at((2, 2))
    assert scenery is not None

    assert [action.action_id for action in manager.get_actions(scenery)] == ["walk", "examine", "cancel"]

    manager.perform_action("examine", scenery)
    manager.perform_action("walk", scenery)

    assert feedback[-2:] == ["Signpost", "Walking here"]
    assert player.path[-1] == (2, 2)


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


def test_cancel_action_stops_pending_gathering() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [_tree().to_dict()],
        }
    )
    inventory = Inventory({"bronze_axe": 1})
    skills = Skills(_skills())
    gathering = GatheringSystem(world.resource_nodes, inventory, skills, time_provider=lambda: 100.0)
    manager = InteractionManager(
        world,
        _Player(tile=(1, 2)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        lambda message: None,
        gathering=gathering,
    )
    tree = world.get_object("tree_01")

    manager.interact_with(tree)
    manager.perform_action("cancel", tree)

    assert gathering.pending is None


def test_combat_start_cancels_pending_gathering() -> None:
    clock = FakeClock()
    world = WorldMap(
        {
            "width": 5,
            "height": 5,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [_tree().to_dict()],
            "mobs": [{**_mob_data(), "position": [1, 1]}],
        }
    )
    inventory = Inventory({"bronze_axe": 1})
    skills = Skills(_skills())
    gathering = GatheringSystem(world.resource_nodes, inventory, skills, time_provider=clock)
    combat = CombatSystem(world.mob_definitions, time_provider=clock)
    manager = InteractionManager(
        world,
        _Player(tile=(1, 2)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        lambda message: None,
        gathering=gathering,
        combat=combat,
    )

    manager.interact_with(world.get_object("tree_01"))
    assert gathering.pending is not None
    manager.interact_with(world.get_object("mob_01"))

    assert gathering.pending is None
    assert combat.pending is not None


def test_missing_gathering_target_stops_activity() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [_tree().to_dict()],
        }
    )
    inventory = Inventory({"bronze_axe": 1})
    skills = Skills(_skills())
    gathering = GatheringSystem(world.resource_nodes, inventory, skills, time_provider=lambda: 100.0)
    feedback: list[str] = []
    manager = InteractionManager(
        world,
        _Player(tile=(1, 2)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        gathering=gathering,
    )

    manager.interact_with(world.get_object("tree_01"))
    world.objects.pop("tree_01")
    manager.update()

    assert gathering.pending is None
    assert feedback[-1] == "Gathering stopped"


def test_gathering_animation_starts_and_move_cancels_it() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [_tree().to_dict()],
        }
    )
    inventory = Inventory({"bronze_axe": 1})
    skills = Skills(_skills())
    gathering = GatheringSystem(world.resource_nodes, inventory, skills, time_provider=lambda: 100.0)
    animator = _Animator()
    player = _Player(tile=(1, 2))
    manager = InteractionManager(
        world,
        player,
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        lambda message: None,
        gathering=gathering,
        animator=animator,
    )
    tree = world.get_object("tree_01")
    assert tree is not None
    tree.node = _AnimNode()

    manager.interact_with(tree)

    assert gathering.pending is not None
    assert ("start_shake", "action:target_shake") in animator.calls
    assert ("start_tilt", "action:target") in animator.calls
    assert ("start_pulse", "action:target_pulse") in animator.calls

    manager.move_to_tile((0, 0))

    assert gathering.pending is None
    assert "action:" in animator.stopped_prefixes


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


def test_multiple_smithing_matches_request_recipe_choice() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [],
            "anvil": {"id": "anvil_01", "tile": [1, 2]},
        }
    )
    inventory = Inventory({"bronze_bar": 2})
    skills = Skills(_skills())
    smithing = SmithingSystem(_recipes(), inventory, skills)
    feedback: list[str] = []
    choices: list[tuple[str, list[str]]] = []
    manager = InteractionManager(
        world,
        _Player(tile=(1, 1)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        smithing=smithing,
        on_smithing_choice=lambda action_type, recipes: choices.append(
            (action_type, [recipe.recipe_id for recipe in recipes])
        ),
    )

    manager.select_inventory_item("bronze_bar")
    manager.interact_with(world.get_object("anvil_01"))

    assert feedback[-1] == "Choose a recipe to smith"
    assert choices == [("smithing", ["bronze_sword", "bronze_shield"])]
    assert smithing.pending is None


def test_selected_smithing_recipe_starts_exact_recipe() -> None:
    inventory = Inventory({"bronze_bar": 2})
    skills = Skills(_skills())
    smithing = SmithingSystem(_recipes(), inventory, skills)
    feedback: list[str] = []
    manager = InteractionManager(
        SimpleNamespace(),
        SimpleNamespace(tile=(0, 0)),
        inventory,
        skills,
        Shop(_items()),
        lambda amount: None,
        feedback.append,
        smithing=smithing,
    )

    manager.start_smithing_recipe("smithing", "bronze_shield")

    assert smithing.pending is not None
    assert smithing.pending.recipe_id == "bronze_shield"
    assert feedback[-1] == "Smithing Bronze shield... 2.6s"


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
    assert feedback[-1] == "Attacking Worn dummy: 2/2 HP; you: 10/10 HP; 1.0s"

    clock.now += 1.0
    manager.update()
    clock.now += 1.0
    manager.update()

    assert world.get_object("mob_01").active is False
    ground_items = [obj for obj in world.objects.values() if obj.kind == "ground_item"]
    assert [obj.item_id for obj in ground_items] == ["coins", "wooden_splinters"]
    assert feedback[-1] == "Defeated Worn dummy; you: 9/10 HP; drops appeared"

    manager.interact_with(ground_items[0])

    assert inventory.count("coins") == 3
    assert world.get_object(ground_items[0].object_id) is None


def _skills() -> dict[str, dict[str, object]]:
    return {
        "woodcutting": {
            "display_name": "Woodcutting",
            "starting_level": 1,
            "xp_thresholds": skill_xp_thresholds(),
        },
        "cooking": {
            "display_name": "Cooking",
            "starting_level": 1,
            "xp_thresholds": skill_xp_thresholds(),
        },
        "smithing": {
            "display_name": "Smithing",
            "starting_level": 1,
            "xp_thresholds": skill_xp_thresholds(),
        },
        "fishing": {
            "display_name": "Fishing",
            "starting_level": 1,
            "xp_thresholds": skill_xp_thresholds(),
        },
    }


def _items() -> dict[str, dict[str, object]]:
    return {
        "coins": {"name": "Coins", "category": "currency", "sell_price": 0, "stackable": True},
        "logs": {"name": "Logs", "category": "wood", "sell_price": 3, "stackable": False},
        "bronze_bar": {"name": "Bronze bar", "category": "bar", "sell_price": 12, "stackable": False},
        "bronze_sword": {"name": "Bronze sword", "category": "weapon", "sell_price": 24, "stackable": False},
        "bronze_shield": {"name": "Bronze shield", "category": "armor", "sell_price": 30, "stackable": False},
        "fishing_rod": {
            "name": "Fishing rod",
            "category": "tool",
            "sell_price": 18,
            "stackable": False,
            "tool_for": "fishing",
        },
        "raw_shrimp": {
            "name": "Raw shrimp",
            "category": "fish",
            "sell_price": 4,
            "stackable": False,
            "cook_result": "cooked_shrimp",
            "cooking_required_level": 1,
            "cooking_xp": 30,
            "base_cook_seconds": 1.8,
        },
        "cooked_shrimp": {"name": "Cooked shrimp", "category": "fish", "sell_price": 7, "stackable": False},
    }


def _recipes() -> dict[str, object]:
    return {
        "smelting": [],
        "smithing": [
            {
                "recipe_id": "bronze_sword",
                "display_name": "Bronze sword",
                "inputs": {"bronze_bar": 1},
                "output_item_id": "bronze_sword",
                "output_quantity": 1,
                "required_level": 1,
                "xp_reward": 12,
                "base_seconds": 2.0,
            },
            {
                "recipe_id": "bronze_shield",
                "display_name": "Bronze shield",
                "inputs": {"bronze_bar": 2},
                "output_item_id": "bronze_shield",
                "output_quantity": 1,
                "required_level": 1,
                "xp_reward": 24,
                "base_seconds": 2.6,
            },
        ],
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


class _ClickInteractions:
    def __init__(self) -> None:
        self.interacted: list[WorldObject] = []
        self.moved: list[tuple[int, int]] = []

    def interact_with(self, obj: WorldObject) -> None:
        self.interacted.append(obj)

    def move_to_tile(self, tile: tuple[int, int]) -> None:
        self.moved.append(tile)


class _Animator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.stopped_prefixes: list[str] = []

    def stop_prefix(self, prefix: str) -> int:
        self.stopped_prefixes.append(prefix)
        return 0

    def start_tilt(self, key: str, node: object, **_kwargs: object) -> None:
        self.calls.append(("start_tilt", key))

    def start_pulse(self, key: str, node: object, **_kwargs: object) -> None:
        self.calls.append(("start_pulse", key))

    def start_shake(self, key: str, node: object, **_kwargs: object) -> None:
        self.calls.append(("start_shake", key))


class _AnimNode:
    pass


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
