from __future__ import annotations

from copy import deepcopy

import pytest

from game.engine.validation import DataValidationError, validate_all


def test_data_validation_success() -> None:
    validate_all(_items(), _skills(), _world())


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


def _items() -> dict[str, dict[str, object]]:
    return {
        "logs": {"name": "Logs", "category": "wood", "sell_price": 3},
        "copper_ore": {"name": "Copper ore", "category": "ore", "sell_price": 5},
        "raw_shrimp": {"name": "Raw shrimp", "category": "fish", "sell_price": 4},
    }


def _skills() -> dict[str, dict[str, object]]:
    return {
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
    }
