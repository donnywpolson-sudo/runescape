from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from game import settings


@dataclass(frozen=True)
class ValidationIssue:
    source: str
    message: str

    def __str__(self) -> str:
        return f"{self.source}: {self.message}"


class DataValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("\n".join(str(issue) for issue in issues))


def validate_data_dir(data_dir: str | Path = settings.DATA_DIR) -> None:
    root = Path(data_dir)
    items = _load_json(root / "items.json")
    skills = _load_json(root / "skills.json")
    world = _load_json(root / "world.json")
    validate_all(items, skills, world)


def validate_all(
    items: dict[str, Any],
    skills: dict[str, Any],
    world: dict[str, Any],
) -> None:
    issues: list[ValidationIssue] = []
    issues.extend(validate_items(items))
    issues.extend(validate_skills(skills))
    issues.extend(validate_world(world, items, skills))
    if issues:
        raise DataValidationError(issues)


def validate_items(items: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(items, dict) or not items:
        return [ValidationIssue("items.json", "must contain at least one item")]

    valid_categories = {"wood", "fish", "ore"}
    for item_id, definition in items.items():
        source = f"items.json:{item_id}"
        if not isinstance(item_id, str) or not item_id:
            issues.append(ValidationIssue("items.json", "item IDs must be non-empty strings"))
        if not isinstance(definition, dict):
            issues.append(ValidationIssue(source, "definition must be an object"))
            continue
        if not isinstance(definition.get("name"), str) or not definition.get("name"):
            issues.append(ValidationIssue(source, "missing required string 'name'"))
        sell_price = definition.get("sell_price", 0)
        if not isinstance(sell_price, int) or sell_price < 0:
            issues.append(ValidationIssue(source, "'sell_price' must be a non-negative integer"))
        category = definition.get("category")
        if category not in valid_categories:
            issues.append(ValidationIssue(source, "'category' must be one of: fish, ore, wood"))
    return issues


def validate_skills(skills: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(skills, dict) or not skills:
        return [ValidationIssue("skills.json", "must contain at least one skill")]

    for skill_id, definition in skills.items():
        source = f"skills.json:{skill_id}"
        if not isinstance(definition, dict):
            issues.append(ValidationIssue(source, "definition must be an object"))
            continue
        if not isinstance(definition.get("display_name"), str) or not definition.get("display_name"):
            issues.append(ValidationIssue(source, "missing required string 'display_name'"))
        starting_level = definition.get("starting_level")
        if not isinstance(starting_level, int) or starting_level < 1:
            issues.append(ValidationIssue(source, "'starting_level' must be a positive integer"))
        thresholds = definition.get("xp_thresholds")
        if not isinstance(thresholds, dict) or not thresholds:
            issues.append(ValidationIssue(source, "missing required object 'xp_thresholds'"))
            continue
        parsed: list[tuple[int, int]] = []
        for raw_level, raw_xp in thresholds.items():
            try:
                level = int(raw_level)
            except (TypeError, ValueError):
                issues.append(ValidationIssue(source, "XP threshold levels must be integers"))
                continue
            if not isinstance(raw_xp, int):
                issues.append(ValidationIssue(source, "XP threshold values must be integers"))
                continue
            parsed.append((level, raw_xp))
        parsed.sort()
        if not parsed or parsed[0] != (1, 0):
            issues.append(ValidationIssue(source, "XP thresholds must start with level 1 at 0 XP"))
        previous_xp = -1
        for level, xp in parsed:
            if level < 1 or xp < 0:
                issues.append(ValidationIssue(source, "XP thresholds must be positive levels and non-negative XP"))
            if xp <= previous_xp:
                issues.append(ValidationIssue(source, "XP thresholds must strictly increase"))
            previous_xp = xp
    return issues


def validate_world(
    world: dict[str, Any],
    items: dict[str, Any],
    skills: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(world, dict):
        return [ValidationIssue("world.json", "must contain an object")]

    width = world.get("width")
    height = world.get("height")
    if not isinstance(width, int) or width <= 0:
        issues.append(ValidationIssue("world.json", "'width' must be a positive integer"))
    if not isinstance(height, int) or height <= 0:
        issues.append(ValidationIssue("world.json", "'height' must be a positive integer"))
    if issues:
        return issues

    blocked_tiles = _tile_set(world.get("blocked_tiles", []), "world.json:blocked_tiles", width, height, issues)
    water_tiles = _tile_set(world.get("water_tiles", []), "world.json:water_tiles", width, height, issues)
    player_start = _tile(world.get("player_start"), "world.json:player_start", width, height, issues)
    if player_start is not None and player_start in blocked_tiles:
        issues.append(ValidationIssue("world.json:player_start", "player spawn cannot be blocked"))

    resource_nodes = world.get("resource_nodes")
    if not isinstance(resource_nodes, list) or not resource_nodes:
        issues.append(ValidationIssue("world.json:resource_nodes", "must contain at least one resource node"))
        return issues

    seen_ids: set[str] = set()
    required = {
        "node_id",
        "node_type",
        "skill_id",
        "required_level",
        "xp_reward",
        "item_reward",
        "quantity_reward",
        "position",
        "blocks_movement",
        "depleted_state",
        "base_gather_seconds",
    }
    resource_positions: set[tuple[int, int]] = set()
    for index, node in enumerate(resource_nodes):
        source = f"world.json:resource_nodes[{index}]"
        if not isinstance(node, dict):
            issues.append(ValidationIssue(source, "resource node must be an object"))
            continue
        missing = sorted(required - set(node))
        if missing:
            issues.append(ValidationIssue(source, f"missing required keys: {', '.join(missing)}"))
            continue
        node_id = node.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            issues.append(ValidationIssue(source, "'node_id' must be a non-empty string"))
        elif node_id in seen_ids:
            issues.append(ValidationIssue(source, f"duplicate resource node ID '{node_id}'"))
        else:
            seen_ids.add(node_id)
        if node.get("skill_id") not in skills:
            issues.append(ValidationIssue(source, f"unknown skill_id '{node.get('skill_id')}'"))
        if node.get("item_reward") not in items:
            issues.append(ValidationIssue(source, f"unknown item_reward '{node.get('item_reward')}'"))
        for key in ("required_level", "xp_reward", "quantity_reward"):
            if not isinstance(node.get(key), int) or int(node.get(key)) < (1 if key != "xp_reward" else 0):
                issues.append(ValidationIssue(source, f"'{key}' must be a valid integer"))
        if not isinstance(node.get("blocks_movement"), bool):
            issues.append(ValidationIssue(source, "'blocks_movement' must be a boolean"))
        if not isinstance(node.get("depleted_state"), str) or not node.get("depleted_state"):
            issues.append(ValidationIssue(source, "'depleted_state' must be a non-empty string"))
        display_name = node.get("display_name")
        if display_name is not None and (not isinstance(display_name, str) or not display_name):
            issues.append(ValidationIssue(source, "'display_name' must be a non-empty string"))
        respawn_seconds = node.get("respawn_seconds")
        if respawn_seconds is not None and (
            not isinstance(respawn_seconds, (int, float)) or respawn_seconds < 0
        ):
            issues.append(ValidationIssue(source, "'respawn_seconds' must be a non-negative number"))
        base_gather_seconds = node.get("base_gather_seconds")
        if not isinstance(base_gather_seconds, (int, float)) or base_gather_seconds <= 0:
            issues.append(ValidationIssue(source, "'base_gather_seconds' must be a positive number"))
        position = _tile(node.get("position"), f"{source}.position", width, height, issues)
        if position is not None and player_start == position and node.get("blocks_movement"):
            issues.append(ValidationIssue(source, "blocking resource cannot overlap player spawn"))
        if position is not None:
            resource_positions.add(position)

    _validate_optional_world_object(
        world,
        "bank",
        width,
        height,
        blocked_tiles | water_tiles,
        player_start,
        resource_positions,
        issues,
    )
    return issues


def _validate_optional_world_object(
    world: dict[str, Any],
    key: str,
    width: int,
    height: int,
    blocked_tiles: set[tuple[int, int]],
    player_start: tuple[int, int] | None,
    resource_positions: set[tuple[int, int]],
    issues: list[ValidationIssue],
) -> None:
    raw_object = world.get(key)
    if raw_object is None:
        return

    source = f"world.json:{key}"
    if not isinstance(raw_object, dict):
        issues.append(ValidationIssue(source, "must be an object"))
        return

    object_id = raw_object.get("id")
    if not isinstance(object_id, str) or not object_id:
        issues.append(ValidationIssue(source, "missing required string 'id'"))

    tile = _tile(raw_object.get("tile"), f"{source}.tile", width, height, issues)
    if tile is None:
        return
    if tile in blocked_tiles:
        issues.append(ValidationIssue(source, "tile cannot overlap blocked or water tile"))
    if tile == player_start:
        issues.append(ValidationIssue(source, "tile cannot overlap player spawn"))
    if tile in resource_positions:
        issues.append(ValidationIssue(source, "tile cannot overlap a resource node"))


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DataValidationError([ValidationIssue(path.name, "top-level JSON value must be an object")])
    return data


def _tile_set(
    raw_tiles: Any,
    source: str,
    width: int,
    height: int,
    issues: list[ValidationIssue],
) -> set[tuple[int, int]]:
    if not isinstance(raw_tiles, list):
        issues.append(ValidationIssue(source, "must be a list"))
        return set()
    tiles: set[tuple[int, int]] = set()
    for index, raw_tile in enumerate(raw_tiles):
        tile = _tile(raw_tile, f"{source}[{index}]", width, height, issues)
        if tile is not None:
            tiles.add(tile)
    return tiles


def _tile(
    raw_tile: Any,
    source: str,
    width: int,
    height: int,
    issues: list[ValidationIssue],
) -> tuple[int, int] | None:
    if (
        not isinstance(raw_tile, list)
        or len(raw_tile) != 2
        or not all(isinstance(value, int) for value in raw_tile)
    ):
        issues.append(ValidationIssue(source, "must be a two-integer tile"))
        return None
    tile = (int(raw_tile[0]), int(raw_tile[1]))
    if not (0 <= tile[0] < width and 0 <= tile[1] < height):
        issues.append(ValidationIssue(source, "tile is out of bounds"))
        return None
    return tile
