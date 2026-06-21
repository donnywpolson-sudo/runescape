from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from game.engine.save import LEGACY_ITEM_ID_ALIASES, LEGACY_RESOURCE_ID_ALIASES
from game.engine.validation import DataValidationError, validate_all
from game.systems.skills import skill_xp_thresholds


def test_data_validation_success() -> None:
    validate_all(_items(), _skills(), _world(), quests=_quests())


def test_data_validation_missing_required_resource_keys() -> None:
    world = _world()
    world["resource_nodes"][0].pop("base_gather_seconds")

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "missing required keys" in str(exc.value)


def test_data_validation_missing_item_category() -> None:
    items = _items()
    items["logs"].pop("category")

    with pytest.raises(DataValidationError) as exc:
        validate_all(items, _skills(), _world())

    assert "'category' must be one of" in str(exc.value)


def test_data_validation_requires_boolean_stackable() -> None:
    items = _items()
    items["logs"]["stackable"] = "no"

    with pytest.raises(DataValidationError) as exc:
        validate_all(items, _skills(), _world())

    assert "'stackable' must be a boolean" in str(exc.value)


def test_data_validation_incomplete_cooking_metadata() -> None:
    items = _items()
    items["raw_shrimp"].pop("base_cook_seconds")

    with pytest.raises(DataValidationError) as exc:
        validate_all(items, _skills(), _world())

    assert "cooking items must include" in str(exc.value)


def test_data_validation_invalid_resource_display_name() -> None:
    world = _world()
    world["resource_nodes"][0]["display_name"] = ""

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "'display_name' must be a non-empty string" in str(exc.value)


def test_data_validation_duplicate_resource_node_ids() -> None:
    world = _world()
    duplicate = deepcopy(world["resource_nodes"][0])
    world["resource_nodes"].append(duplicate)

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "duplicate resource node ID" in str(exc.value)


def test_data_validation_invalid_player_spawn() -> None:
    world = _world()
    world["player_start"] = [1, 1]
    world["blocked_tiles"] = [[1, 1]]

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "player spawn cannot be blocked" in str(exc.value)


def test_data_validation_invalid_xp_thresholds() -> None:
    skills = _skills()
    skills["mining"]["xp_thresholds"] = {"1": 10, "2": 5}

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), skills, _world())

    assert "XP thresholds" in str(exc.value)


def test_data_validation_invalid_bank_tile() -> None:
    world = _world()
    world["bank"] = {"id": "bank_01", "tile": [99, 99]}

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "world.json:bank.tile" in str(exc.value)


def test_data_validation_invalid_cooking_range_tile() -> None:
    world = _world()
    world["cooking_range"] = {"id": "cooking_range_01", "tile": [10, 11]}

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "world.json:cooking_range" in str(exc.value)


def test_data_validation_accepts_decorations() -> None:
    world = _world()
    world["decorations"] = [
        {"id": "dock_01", "kind": "dock", "position": [1, 1], "rotation": 90},
        {"id": "fence_01", "kind": "fence", "position": [12, 12], "blocking": True},
    ]

    validate_all(_items(), _skills(), world)


def test_data_validation_rejects_blocking_decoration_on_resource() -> None:
    world = _world()
    world["decorations"] = [
        {"id": "fence_01", "kind": "fence", "position": [10, 11], "blocking": True}
    ]

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "blocking decoration cannot overlap" in str(exc.value)


def test_data_validation_rejects_duplicate_decoration_id() -> None:
    world = _world()
    world["decorations"] = [
        {"id": "tree_01", "kind": "signpost", "position": [1, 1]}
    ]

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "duplicate object ID 'tree_01'" in str(exc.value)


def test_data_validation_accepts_shop_stock_fishing_water_and_mobs() -> None:
    world = _world()
    world["water_tiles"] = [[4, 4]]
    world["resource_nodes"].append(_fish_node([4, 4]))
    world["shop"] = {
        "id": "shop_01",
        "tile": [11, 11],
        "stock": [{"item_id": "bronze_axe", "price": 25}],
    }
    world["mobs"] = [_mob()]

    validate_all(_items(), _skills(), world)


def test_data_validation_accepts_ranged_and_magic_weapon_requirements() -> None:
    items = _items()
    items["training_bow"] = {
        "name": "Training bow",
        "category": "weapon",
        "stackable": False,
        "sell_price": 10,
        "ranged_bonus": 1,
        "equip_slot": "weapon",
        "required_skills": {"ranged": 1},
    }
    items["training_staff"] = {
        "name": "Training staff",
        "category": "weapon",
        "stackable": False,
        "sell_price": 10,
        "magic_bonus": 1,
        "equip_slot": "weapon",
        "required_skills": {"magic": 1},
    }

    validate_all(items, _skills(), _world())


def test_data_validation_rejects_active_skill_refs_missing_from_skill_data() -> None:
    items = _items()
    items["training_bow"] = {
        "name": "Training bow",
        "category": "weapon",
        "stackable": False,
        "sell_price": 10,
        "ranged_bonus": 1,
        "equip_slot": "weapon",
        "required_skills": {"ranged": 1},
    }
    world = _world()
    mob = _mob()
    mob["attack_style"] = "ranged"
    mob["attack_range"] = 4
    world["mobs"] = [mob]
    skills = _skills()
    skills.pop("ranged")

    with pytest.raises(DataValidationError) as exc:
        validate_all(items, skills, world)

    message = str(exc.value)
    assert "missing required skill 'ranged'" in message
    assert "unknown required skill 'ranged'" in message
    assert "unknown combat skill 'ranged'" in message


def test_data_validation_accepts_recipes_npcs_and_smithing_stations() -> None:
    world = _world()
    world["furnace"] = {"id": "furnace_01", "tile": [16, 16]}
    world["anvil"] = {"id": "anvil_01", "tile": [17, 16]}
    world["npcs"] = [{"id": "guide_01", "name": "Village Guide", "tile": [18, 16], "quest_id": "starter_path"}]

    validate_all(_items(), _skills(), world, _recipes(), _quests())


def test_data_validation_rejects_unknown_npc_quest_id_when_quests_loaded() -> None:
    world = _world()
    world["npcs"] = [{"id": "guide_01", "name": "Village Guide", "tile": [18, 16], "quest_id": "missing_path"}]

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world, quests=_quests())

    assert "unknown quest_id 'missing_path'" in str(exc.value)


def test_data_validation_accepts_quests() -> None:
    validate_all(_items(), _skills(), _world(), quests=_quests())


def test_data_validation_rejects_unknown_quest_reward_item() -> None:
    quests = _quests()
    quests["quests"][0]["item_rewards"][0]["item_id"] = "missing_item"

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), _world(), quests=quests)

    assert "unknown item_id 'missing_item'" in str(exc.value)


def test_data_validation_rejects_unknown_quest_reward_skill() -> None:
    quests = _quests()
    quests["quests"][0]["skill_rewards"][0]["skill_id"] = "missing_skill"

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), _world(), quests=quests)

    assert "unknown skill_id 'missing_skill'" in str(exc.value)


def test_data_validation_rejects_duplicate_quest_objective_flags() -> None:
    quests = _quests()
    quests["quests"][0]["objectives"][1]["flag"] = "cooked_food"

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), _world(), quests=quests)

    assert "duplicate objective flag 'cooked_food'" in str(exc.value)


def test_data_validation_rejects_unknown_recipe_input() -> None:
    recipes = _recipes()
    recipes["smelting"][0]["inputs"] = {"missing_ore": 1}

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), _world(), recipes)

    assert "unknown input item 'missing_ore'" in str(exc.value)


def test_data_validation_rejects_fishing_node_off_water() -> None:
    world = _world()
    world["water_tiles"] = [[4, 4]]
    world["resource_nodes"].append(_fish_node([5, 5]))

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "fishing resource must be placed on a water tile" in str(exc.value)


def test_data_validation_rejects_bad_shop_stock_item() -> None:
    world = _world()
    world["shop"] = {
        "id": "shop_01",
        "tile": [11, 11],
        "stock": [{"item_id": "missing_tool", "price": 25}],
    }

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "unknown item_id 'missing_tool'" in str(exc.value)


def test_data_validation_rejects_unknown_mob_drop() -> None:
    world = _world()
    mob = _mob()
    mob["drops"] = [{"item_id": "missing_drop", "quantity": 1}]
    world["mobs"] = [mob]

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    assert "unknown item_id 'missing_drop'" in str(exc.value)


def test_data_validation_rejects_invalid_mob_combat_profile() -> None:
    world = _world()
    mob = _mob()
    mob["attack_style"] = "shouting"
    mob["attack_range"] = 0
    world["mobs"] = [mob]

    with pytest.raises(DataValidationError) as exc:
        validate_all(_items(), _skills(), world)

    message = str(exc.value)
    assert "'attack_style' must be melee, ranged, or magic" in message
    assert "'attack_range' must be a positive integer" in message


def test_data_validation_rejects_protected_terms_in_active_content() -> None:
    items = _items()
    items["runite_ore"] = {
        "name": "Forbidden ore",
        "category": "ore",
        "sell_price": 1,
        "stackable": False,
    }

    with pytest.raises(DataValidationError) as exc:
        validate_all(items, _skills(), _world(), quests=_quests())

    message = str(exc.value)
    assert "items.json:runite_ore" in message
    assert "contains protected or near-branded term 'runite'" in message


def test_shipped_high_tier_content_uses_original_starsteel_ids() -> None:
    items = _load_data("items.json")
    recipes = _load_data("recipes.json")
    world = _load_data("world.json")

    assert items["starsteel_sword"]["name"] == "Starsteel sword"
    assert items["starsteel_shield"]["name"] == "Starsteel shield"
    assert items["starsteel_ore"]["name"] == "Starsteel ore"
    assert items["starsteel_bar"]["name"] == "Starsteel bar"

    recipe_ids = {
        recipe["recipe_id"]
        for recipe_group in recipes.values()
        for recipe in recipe_group
    }
    assert {"starsteel_bar", "starsteel_sword", "starsteel_shield"} <= recipe_ids

    node = next(
        node
        for node in world["resource_nodes"]
        if node["node_id"] == "starsteel_rock_01"
    )
    assert node["display_name"] == "Starsteel rock"
    assert node["item_reward"] == "starsteel_ore"


def test_shipped_skills_include_explicit_ranged_and_magic_entries() -> None:
    skills = _load_data("skills.json")

    assert skills["ranged"]["display_name"] == "Ranged"
    assert skills["ranged"]["starting_level"] == 1
    assert skills["ranged"]["xp_thresholds"]["99"] == skill_xp_thresholds()["99"]
    assert skills["magic"]["display_name"] == "Magic"
    assert skills["magic"]["starting_level"] == 1
    assert skills["magic"]["xp_thresholds"]["99"] == skill_xp_thresholds()["99"]


def test_legacy_save_migration_aliases_remain_compatibility_only() -> None:
    assert LEGACY_ITEM_ID_ALIASES["runite_ore"] == "starsteel_ore"
    assert LEGACY_RESOURCE_ID_ALIASES["runite_rock_01"] == "starsteel_rock_01"

    validate_all(_items(), _skills(), _world(), quests=_quests())


def test_shipped_world_has_no_non_useful_decorations() -> None:
    world = _load_data("world.json")

    assert world.get("decorations") == []


def test_shipped_world_has_phase_one_monster_roster() -> None:
    items = _load_data("items.json")
    world = _load_data("world.json")
    mobs = {mob["mob_id"]: mob for mob in world["mobs"]}

    assert set(mobs) == {
        "rat_01",
        "goblin_01",
        "skeleton_01",
        "slime_01",
        "wolf_01",
        "bandit_01",
        "mage_imp_01",
        "archer_goblin_01",
    }
    assert mobs["mage_imp_01"]["attack_style"] == "magic"
    assert mobs["mage_imp_01"]["attack_range"] == 4
    assert mobs["archer_goblin_01"]["attack_style"] == "ranged"
    assert mobs["archer_goblin_01"]["attack_range"] == 4
    assert {"bones", "cloth", "gel"} <= set(items)


def test_shipped_fishing_nodes_use_generic_spot_names() -> None:
    world = _load_data("world.json")
    fishing_nodes = [
        node
        for node in world["resource_nodes"]
        if str(node["skill_id"]) == "fishing"
    ]

    assert fishing_nodes
    assert {node["display_name"] for node in fishing_nodes} == {"Fishing spot"}


def test_shipped_trail_supplies_quest_links_to_original_npc() -> None:
    items = _load_data("items.json")
    skills = _load_data("skills.json")
    recipes = _load_data("recipes.json")
    quests = _load_data("quests.json")
    world = _load_data("world.json")

    validate_all(items, skills, world, recipes, quests)

    quest_ids = {quest["quest_id"] for quest in quests["quests"]}
    npcs_by_id = {npc["id"]: npc for npc in world["npcs"]}

    assert "trail_supplies" in quest_ids
    assert npcs_by_id["trail_warden_01"]["name"] == "Trail Warden"
    assert npcs_by_id["trail_warden_01"]["quest_id"] == "trail_supplies"
    assert "field_provisions" in quest_ids
    assert npcs_by_id["field_steward_01"]["name"] == "Field Steward"
    assert npcs_by_id["field_steward_01"]["quest_id"] == "field_provisions"


def _items() -> dict[str, dict[str, object]]:
    return {
        "coins": {"name": "Coins", "category": "currency", "sell_price": 0, "stackable": True},
        "bronze_axe": {"name": "Bronze axe", "category": "tool", "sell_price": 8, "stackable": False},
        "logs": {"name": "Logs", "category": "wood", "sell_price": 3, "stackable": False},
        "copper_ore": {"name": "Copper ore", "category": "ore", "sell_price": 5, "stackable": False},
        "tin_ore": {"name": "Tin ore", "category": "ore", "sell_price": 5, "stackable": False},
        "bronze_bar": {"name": "Bronze bar", "category": "bar", "sell_price": 12, "stackable": False},
        "bronze_sword": {
            "name": "Bronze sword",
            "category": "weapon",
            "sell_price": 18,
            "stackable": False,
            "equip_slot": "weapon",
            "attack_bonus": 1,
            "strength_bonus": 1,
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
        "wooden_splinters": {
            "name": "Wooden splinters",
            "category": "misc",
            "sell_price": 1,
            "stackable": False,
        },
    }


def _skills() -> dict[str, dict[str, object]]:
    thresholds = skill_xp_thresholds()
    return {
        "woodcutting": {
            "display_name": "Woodcutting",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "mining": {
            "display_name": "Mining",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "fishing": {
            "display_name": "Fishing",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "cooking": {
            "display_name": "Cooking",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "attack": {
            "display_name": "Attack",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "strength": {
            "display_name": "Strength",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "defence": {
            "display_name": "Defence",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "ranged": {
            "display_name": "Ranged",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "magic": {
            "display_name": "Magic",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
        "hitpoints": {
            "display_name": "Hitpoints",
            "starting_level": 10,
            "xp_thresholds": thresholds,
        },
        "smithing": {
            "display_name": "Smithing",
            "starting_level": 1,
            "xp_thresholds": thresholds,
        },
    }


def _world() -> dict[str, object]:
    return {
        "width": 30,
        "height": 30,
        "player_start": [15, 15],
        "blocked_tiles": [],
        "resource_nodes": [
            {
                "node_id": "tree_01",
                "node_type": "tree",
                "display_name": "Tree",
                "skill_id": "woodcutting",
                "required_level": 1,
                "xp_reward": 25,
                "item_reward": "logs",
                "quantity_reward": 1,
                "position": [10, 11],
                "blocks_movement": True,
                "depleted_state": "stump",
                "base_gather_seconds": 1.0,
            }
        ],
        "bank": {"id": "bank_01", "tile": [13, 14]},
        "cooking_range": {"id": "cooking_range_01", "tile": [14, 14]},
    }


def _fish_node(position: list[int]) -> dict[str, object]:
    return {
        "node_id": "shrimp_spot_01",
        "node_type": "shrimp_spot",
        "display_name": "Raw shrimp",
        "skill_id": "fishing",
        "required_level": 1,
        "xp_reward": 15,
        "item_reward": "raw_shrimp",
        "quantity_reward": 1,
        "position": position,
        "blocks_movement": False,
        "depleted_state": "quiet_water",
        "base_gather_seconds": 1.0,
    }


def _mob() -> dict[str, object]:
    return {
        "mob_id": "mob_01",
        "display_name": "Test sentry",
        "level": 1,
        "hitpoints": 2,
        "attack_seconds": 1.0,
        "respawn_seconds": 5.0,
        "position": [12, 12],
        "drops": [{"item_id": "wooden_splinters", "quantity": 1}],
    }


def _recipes() -> dict[str, object]:
    return {
        "smelting": [
            {
                "recipe_id": "bronze_bar",
                "display_name": "Bronze bar",
                "inputs": {"copper_ore": 1, "tin_ore": 1},
                "output_item_id": "bronze_bar",
                "output_quantity": 1,
                "required_level": 1,
                "xp_reward": 6,
                "base_seconds": 1.8,
            }
        ],
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
            }
        ],
    }


def _quests() -> dict[str, object]:
    return {
        "quests": [
            {
                "quest_id": "starter_path",
                "display_name": "Starter path",
                "start_text": "Guide: Cook food and help the village.",
                "in_progress_text": "Guide: Keep going. Still needed: {missing_objectives}.",
                "completed_text": "Guide: The village is safer because of you.",
                "completion_text": "Quest complete: Starter path. Reward: 50 coins, +40 Smithing XP.",
                "not_started_objective": "Talk to the Village Guide.",
                "return_objective": "Return to the Village Guide.",
                "completed_objective": "Starter path complete.",
                "progress_format": "Starter path {completed}/{total}: {objective}.",
                "objectives": [
                    {"flag": "cooked_food", "label": "Cook food"},
                    {"flag": "smelted_bar", "label": "Smelt a bar"},
                ],
                "item_rewards": [{"item_id": "coins", "quantity": 50}],
                "skill_rewards": [{"skill_id": "smithing", "xp": 40}],
            }
        ]
    }


def _load_data(filename: str) -> dict[str, object]:
    path = Path(__file__).resolve().parents[1] / "game" / "data" / filename
    return json.loads(path.read_text(encoding="utf-8"))
