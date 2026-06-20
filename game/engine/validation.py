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
    recipes_path = root / "recipes.json"
    recipes = _load_json(recipes_path) if recipes_path.exists() else None
    validate_all(items, skills, world, recipes)


def validate_all(
    items: dict[str, Any],
    skills: dict[str, Any],
    world: dict[str, Any],
    recipes: dict[str, Any] | None = None,
) -> None:
    issues: list[ValidationIssue] = []
    issues.extend(validate_items(items))
    issues.extend(validate_skills(skills))
    issues.extend(validate_item_skill_refs(items, skills))
    issues.extend(validate_world(world, items, skills))
    if recipes is not None:
        issues.extend(validate_recipes(recipes, items, skills))
    if issues:
        raise DataValidationError(issues)


def validate_items(items: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(items, dict) or not items:
        return [ValidationIssue("items.json", "must contain at least one item")]

    valid_categories = {"armor", "bar", "currency", "fish", "misc", "ore", "tool", "weapon", "wood"}
    cooking_keys = {"cook_result", "cooking_required_level", "cooking_xp", "base_cook_seconds"}
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
            issues.append(
                ValidationIssue(
                    source,
                    "'category' must be one of: armor, bar, currency, fish, misc, ore, tool, weapon, wood",
                )
            )
        buy_price = definition.get("buy_price")
        if buy_price is not None and (not isinstance(buy_price, int) or buy_price <= 0):
            issues.append(ValidationIssue(source, "'buy_price' must be a positive integer"))
        heal_amount = definition.get("heal_amount")
        if heal_amount is not None and (not isinstance(heal_amount, int) or heal_amount <= 0):
            issues.append(ValidationIssue(source, "'heal_amount' must be a positive integer"))
        for key in ("attack_bonus", "strength_bonus", "defence_bonus"):
            bonus = definition.get(key)
            if bonus is not None and (not isinstance(bonus, int) or bonus < 0):
                issues.append(ValidationIssue(source, f"'{key}' must be a non-negative integer"))
        equip_slot = definition.get("equip_slot")
        if equip_slot is not None and equip_slot not in {"weapon", "shield"}:
            issues.append(ValidationIssue(source, "'equip_slot' must be one of: shield, weapon"))
        required_skills = definition.get("required_skills")
        if required_skills is not None:
            if not isinstance(required_skills, dict) or not required_skills:
                issues.append(ValidationIssue(source, "'required_skills' must be a non-empty object"))
            else:
                for required_skill, required_level in required_skills.items():
                    if not isinstance(required_skill, str) or not required_skill:
                        issues.append(ValidationIssue(source, "required skill IDs must be non-empty strings"))
                    if not isinstance(required_level, int) or not 1 <= required_level <= 99:
                        issues.append(ValidationIssue(source, "required skill levels must be between 1 and 99"))
        present_cooking_keys = cooking_keys & set(definition)
        if present_cooking_keys and present_cooking_keys != cooking_keys:
            issues.append(
                ValidationIssue(
                    source,
                    "cooking items must include cook_result, cooking_required_level, cooking_xp, and base_cook_seconds",
                )
            )
            continue
        if present_cooking_keys:
            cook_result = definition.get("cook_result")
            if not isinstance(cook_result, str) or not cook_result:
                issues.append(ValidationIssue(source, "'cook_result' must be a non-empty string"))
            elif cook_result not in items:
                issues.append(ValidationIssue(source, f"unknown cook_result '{cook_result}'"))
            elif items.get(cook_result, {}).get("category") != "fish":
                issues.append(ValidationIssue(source, "'cook_result' must refer to a fish item"))
            if category != "fish":
                issues.append(ValidationIssue(source, "cookable items must use category 'fish'"))
            required_level = definition.get("cooking_required_level")
            if not isinstance(required_level, int) or not 1 <= required_level <= 99:
                issues.append(ValidationIssue(source, "'cooking_required_level' must be between 1 and 99"))
            cooking_xp = definition.get("cooking_xp")
            if not isinstance(cooking_xp, int) or cooking_xp <= 0:
                issues.append(ValidationIssue(source, "'cooking_xp' must be a positive integer"))
            base_cook_seconds = definition.get("base_cook_seconds")
            if not isinstance(base_cook_seconds, (int, float)) or base_cook_seconds <= 0:
                issues.append(ValidationIssue(source, "'base_cook_seconds' must be a positive number"))
    return issues


def validate_item_skill_refs(items: dict[str, Any], skills: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    valid_skill_ids = set(skills) | {"attack", "strength", "defence", "hitpoints", "smithing"}
    for item_id, definition in items.items():
        if not isinstance(definition, dict):
            continue
        required_skills = definition.get("required_skills")
        if not isinstance(required_skills, dict):
            continue
        for skill_id in required_skills:
            if skill_id not in valid_skill_ids:
                issues.append(ValidationIssue(f"items.json:{item_id}", f"unknown required skill '{skill_id}'"))
    return issues


def validate_recipes(
    recipes: dict[str, Any],
    items: dict[str, Any],
    skills: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(recipes, dict):
        return [ValidationIssue("recipes.json", "must contain an object")]
    if "smithing" not in skills:
        issues.append(ValidationIssue("skills.json", "missing required skill 'smithing'"))
    for action_type in ("smelting", "smithing"):
        raw_recipes = recipes.get(action_type, [])
        if not isinstance(raw_recipes, list):
            issues.append(ValidationIssue(f"recipes.json:{action_type}", "must be a list"))
            continue
        seen_ids: set[str] = set()
        for index, recipe in enumerate(raw_recipes):
            source = f"recipes.json:{action_type}[{index}]"
            if not isinstance(recipe, dict):
                issues.append(ValidationIssue(source, "recipe must be an object"))
                continue
            required = {"recipe_id", "inputs", "output_item_id", "required_level", "xp_reward", "base_seconds"}
            missing = sorted(required - set(recipe))
            if missing:
                issues.append(ValidationIssue(source, f"missing required keys: {', '.join(missing)}"))
                continue
            recipe_id = recipe.get("recipe_id")
            if not isinstance(recipe_id, str) or not recipe_id:
                issues.append(ValidationIssue(source, "'recipe_id' must be a non-empty string"))
            elif recipe_id in seen_ids:
                issues.append(ValidationIssue(source, f"duplicate recipe ID '{recipe_id}'"))
            else:
                seen_ids.add(recipe_id)
            inputs = recipe.get("inputs")
            if not isinstance(inputs, dict) or not inputs:
                issues.append(ValidationIssue(source, "'inputs' must be a non-empty object"))
            else:
                for item_id, quantity in inputs.items():
                    if item_id not in items:
                        issues.append(ValidationIssue(source, f"unknown input item '{item_id}'"))
                    if not isinstance(quantity, int) or quantity <= 0:
                        issues.append(ValidationIssue(source, "input quantities must be positive integers"))
            output_item_id = recipe.get("output_item_id")
            if not isinstance(output_item_id, str) or output_item_id not in items:
                issues.append(ValidationIssue(source, f"unknown output_item_id '{output_item_id}'"))
            output_quantity = recipe.get("output_quantity", 1)
            if not isinstance(output_quantity, int) or output_quantity <= 0:
                issues.append(ValidationIssue(source, "'output_quantity' must be a positive integer"))
            required_level = recipe.get("required_level")
            if not isinstance(required_level, int) or not 1 <= required_level <= 99:
                issues.append(ValidationIssue(source, "'required_level' must be between 1 and 99"))
            xp_reward = recipe.get("xp_reward")
            if not isinstance(xp_reward, int) or xp_reward <= 0:
                issues.append(ValidationIssue(source, "'xp_reward' must be a positive integer"))
            base_seconds = recipe.get("base_seconds")
            if not isinstance(base_seconds, (int, float)) or base_seconds <= 0:
                issues.append(ValidationIssue(source, "'base_seconds' must be a positive number"))
    return issues


def validate_skills(skills: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(skills, dict) or not skills:
        return [ValidationIssue("skills.json", "must contain at least one skill")]

    required_skills = {"woodcutting", "mining", "fishing", "cooking"}
    missing_skills = sorted(required_skills - set(skills))
    for skill_id in missing_skills:
        issues.append(ValidationIssue("skills.json", f"missing required skill '{skill_id}'"))

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
        parsed_levels = [level for level, _xp in parsed]
        if parsed_levels != list(range(1, 100)):
            issues.append(ValidationIssue(source, "XP thresholds must include every level from 1 to 99"))
        previous_xp = -1
        for level, xp in parsed:
            if not 1 <= level <= 99 or xp < 0:
                issues.append(ValidationIssue(source, "XP thresholds must be levels 1-99 and non-negative XP"))
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
        if isinstance(node.get("required_level"), int) and int(node["required_level"]) > 99:
            issues.append(ValidationIssue(source, "'required_level' must be between 1 and 99"))
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
            if node.get("skill_id") == "fishing":
                if position not in water_tiles:
                    issues.append(ValidationIssue(source, "fishing resource must be placed on a water tile"))
                elif not _has_adjacent_walkable_tile(position, width, height, blocked_tiles | water_tiles):
                    issues.append(ValidationIssue(source, "fishing resource needs adjacent walkable land"))
            elif position in water_tiles:
                issues.append(ValidationIssue(source, "non-fishing resource cannot overlap water tile"))
            resource_positions.add(position)

    world_object_positions: set[tuple[int, int]] = set()
    invalid_object_tiles = blocked_tiles | water_tiles
    for key in ("shop", "bank", "cooking_range", "combat_dummy", "furnace", "anvil"):
        _validate_optional_world_object(
            world,
            key,
            width,
            height,
            invalid_object_tiles,
            player_start,
            resource_positions,
            world_object_positions,
            seen_ids,
            issues,
        )
    _validate_shop_stock(world, items, issues)
    npc_positions = _validate_npcs(
        world,
        width,
        height,
        invalid_object_tiles,
        player_start,
        resource_positions,
        world_object_positions,
        seen_ids,
        issues,
    )
    mob_positions = _validate_mobs(
        world,
        items,
        width,
        height,
        invalid_object_tiles,
        player_start,
        resource_positions,
        world_object_positions,
        seen_ids,
        issues,
    )
    _validate_decorations(
        world,
        width,
        height,
        invalid_object_tiles,
        player_start,
        resource_positions | mob_positions | npc_positions,
        world_object_positions,
        seen_ids,
        issues,
    )
    return issues


def _validate_npcs(
    world: dict[str, Any],
    width: int,
    height: int,
    blocked_tiles: set[tuple[int, int]],
    player_start: tuple[int, int] | None,
    resource_positions: set[tuple[int, int]],
    world_object_positions: set[tuple[int, int]],
    seen_ids: set[str],
    issues: list[ValidationIssue],
) -> set[tuple[int, int]]:
    raw_npcs = world.get("npcs", [])
    npc_positions: set[tuple[int, int]] = set()
    if raw_npcs is None:
        return npc_positions
    if not isinstance(raw_npcs, list):
        issues.append(ValidationIssue("world.json:npcs", "must be a list"))
        return npc_positions

    for index, npc in enumerate(raw_npcs):
        source = f"world.json:npcs[{index}]"
        if not isinstance(npc, dict):
            issues.append(ValidationIssue(source, "npc must be an object"))
            continue
        npc_id = npc.get("id")
        if not isinstance(npc_id, str) or not npc_id:
            issues.append(ValidationIssue(source, "missing required string 'id'"))
        elif npc_id in seen_ids:
            issues.append(ValidationIssue(source, f"duplicate object ID '{npc_id}'"))
        else:
            seen_ids.add(npc_id)
        name = npc.get("name")
        if not isinstance(name, str) or not name:
            issues.append(ValidationIssue(source, "missing required string 'name'"))
        quest_id = npc.get("quest_id")
        if quest_id is not None and (not isinstance(quest_id, str) or not quest_id):
            issues.append(ValidationIssue(source, "'quest_id' must be a non-empty string"))

        tile = _tile(npc.get("tile"), f"{source}.tile", width, height, issues)
        if tile is not None:
            if tile in blocked_tiles:
                issues.append(ValidationIssue(source, "tile cannot overlap blocked or water tile"))
            if tile == player_start:
                issues.append(ValidationIssue(source, "tile cannot overlap player spawn"))
            if tile in resource_positions:
                issues.append(ValidationIssue(source, "tile cannot overlap a resource node"))
            if tile in world_object_positions or tile in npc_positions:
                issues.append(ValidationIssue(source, "tile cannot overlap another world object"))
            npc_positions.add(tile)
    return npc_positions


def _validate_shop_stock(
    world: dict[str, Any],
    items: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    raw_shop = world.get("shop")
    if raw_shop is None or not isinstance(raw_shop, dict):
        return
    stock = raw_shop.get("stock", [])
    if stock is None:
        return
    if not isinstance(stock, list):
        issues.append(ValidationIssue("world.json:shop.stock", "must be a list"))
        return
    for index, raw_stock_item in enumerate(stock):
        source = f"world.json:shop.stock[{index}]"
        if not isinstance(raw_stock_item, dict):
            issues.append(ValidationIssue(source, "stock item must be an object"))
            continue
        item_id = raw_stock_item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            issues.append(ValidationIssue(source, "missing required string 'item_id'"))
        elif item_id not in items:
            issues.append(ValidationIssue(source, f"unknown item_id '{item_id}'"))
        price = raw_stock_item.get("price")
        if price is not None and (not isinstance(price, int) or price <= 0):
            issues.append(ValidationIssue(source, "'price' must be a positive integer"))


def _validate_mobs(
    world: dict[str, Any],
    items: dict[str, Any],
    width: int,
    height: int,
    blocked_tiles: set[tuple[int, int]],
    player_start: tuple[int, int] | None,
    resource_positions: set[tuple[int, int]],
    world_object_positions: set[tuple[int, int]],
    seen_ids: set[str],
    issues: list[ValidationIssue],
) -> set[tuple[int, int]]:
    raw_mobs = world.get("mobs", [])
    mob_positions: set[tuple[int, int]] = set()
    if raw_mobs is None:
        return mob_positions
    if not isinstance(raw_mobs, list):
        issues.append(ValidationIssue("world.json:mobs", "must be a list"))
        return mob_positions

    required = {
        "mob_id",
        "display_name",
        "level",
        "hitpoints",
        "attack_seconds",
        "respawn_seconds",
        "position",
        "drops",
    }
    for index, mob in enumerate(raw_mobs):
        source = f"world.json:mobs[{index}]"
        if not isinstance(mob, dict):
            issues.append(ValidationIssue(source, "mob must be an object"))
            continue
        missing = sorted(required - set(mob))
        if missing:
            issues.append(ValidationIssue(source, f"missing required keys: {', '.join(missing)}"))
            continue

        mob_id = mob.get("mob_id")
        if not isinstance(mob_id, str) or not mob_id:
            issues.append(ValidationIssue(source, "'mob_id' must be a non-empty string"))
        elif mob_id in seen_ids:
            issues.append(ValidationIssue(source, f"duplicate object ID '{mob_id}'"))
        else:
            seen_ids.add(mob_id)

        display_name = mob.get("display_name")
        if not isinstance(display_name, str) or not display_name:
            issues.append(ValidationIssue(source, "'display_name' must be a non-empty string"))
        for key in ("level", "hitpoints"):
            if not isinstance(mob.get(key), int) or int(mob.get(key)) <= 0:
                issues.append(ValidationIssue(source, f"'{key}' must be a positive integer"))
        for key in ("attack_seconds", "respawn_seconds"):
            if not isinstance(mob.get(key), (int, float)) or float(mob.get(key)) <= 0:
                issues.append(ValidationIssue(source, f"'{key}' must be a positive number"))

        tile = _tile(mob.get("position"), f"{source}.position", width, height, issues)
        if tile is not None:
            if tile in blocked_tiles:
                issues.append(ValidationIssue(source, "position cannot overlap blocked or water tile"))
            if tile == player_start:
                issues.append(ValidationIssue(source, "position cannot overlap player spawn"))
            if tile in resource_positions:
                issues.append(ValidationIssue(source, "position cannot overlap a resource node"))
            if tile in world_object_positions:
                issues.append(ValidationIssue(source, "position cannot overlap another world object"))
            if tile in mob_positions:
                issues.append(ValidationIssue(source, "position cannot overlap another mob"))
            mob_positions.add(tile)

        drops = mob.get("drops")
        if not isinstance(drops, list):
            issues.append(ValidationIssue(source, "'drops' must be a list"))
            continue
        for drop_index, drop in enumerate(drops):
            drop_source = f"{source}.drops[{drop_index}]"
            if not isinstance(drop, dict):
                issues.append(ValidationIssue(drop_source, "drop must be an object"))
                continue
            item_id = drop.get("item_id")
            if not isinstance(item_id, str) or not item_id:
                issues.append(ValidationIssue(drop_source, "missing required string 'item_id'"))
            elif item_id not in items:
                issues.append(ValidationIssue(drop_source, f"unknown item_id '{item_id}'"))
            quantity = drop.get("quantity", 1)
            if not isinstance(quantity, int) or quantity <= 0:
                issues.append(ValidationIssue(drop_source, "'quantity' must be a positive integer"))
    return mob_positions


def _validate_optional_world_object(
    world: dict[str, Any],
    key: str,
    width: int,
    height: int,
    blocked_tiles: set[tuple[int, int]],
    player_start: tuple[int, int] | None,
    resource_positions: set[tuple[int, int]],
    world_object_positions: set[tuple[int, int]],
    seen_ids: set[str],
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
    elif object_id in seen_ids:
        issues.append(ValidationIssue(source, f"duplicate object ID '{object_id}'"))
    else:
        seen_ids.add(object_id)

    tile = _tile(raw_object.get("tile"), f"{source}.tile", width, height, issues)
    if tile is None:
        return
    if tile in blocked_tiles:
        issues.append(ValidationIssue(source, "tile cannot overlap blocked or water tile"))
    if tile == player_start:
        issues.append(ValidationIssue(source, "tile cannot overlap player spawn"))
    if tile in resource_positions:
        issues.append(ValidationIssue(source, "tile cannot overlap a resource node"))
    if tile in world_object_positions:
        issues.append(ValidationIssue(source, "tile cannot overlap another world object"))
    world_object_positions.add(tile)


def _validate_decorations(
    world: dict[str, Any],
    width: int,
    height: int,
    blocked_tiles: set[tuple[int, int]],
    player_start: tuple[int, int] | None,
    resource_positions: set[tuple[int, int]],
    world_object_positions: set[tuple[int, int]],
    seen_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    raw_decorations = world.get("decorations", [])
    if raw_decorations is None:
        return
    if not isinstance(raw_decorations, list):
        issues.append(ValidationIssue("world.json:decorations", "must be a list"))
        return

    invalid_blocking_tiles = blocked_tiles | resource_positions | world_object_positions
    if player_start is not None:
        invalid_blocking_tiles.add(player_start)

    for index, decoration in enumerate(raw_decorations):
        source = f"world.json:decorations[{index}]"
        if not isinstance(decoration, dict):
            issues.append(ValidationIssue(source, "decoration must be an object"))
            continue

        decoration_id = decoration.get("id")
        if not isinstance(decoration_id, str) or not decoration_id:
            issues.append(ValidationIssue(source, "missing required string 'id'"))
        elif decoration_id in seen_ids:
            issues.append(ValidationIssue(source, f"duplicate object ID '{decoration_id}'"))
        else:
            seen_ids.add(decoration_id)

        kind = decoration.get("kind")
        if not isinstance(kind, str) or not kind:
            issues.append(ValidationIssue(source, "missing required string 'kind'"))

        tile = _tile(decoration.get("position"), f"{source}.position", width, height, issues)
        rotation = decoration.get("rotation", 0)
        if not isinstance(rotation, (int, float)):
            issues.append(ValidationIssue(source, "'rotation' must be a number"))

        blocking = decoration.get("blocking", False)
        if not isinstance(blocking, bool):
            issues.append(ValidationIssue(source, "'blocking' must be a boolean"))
            continue
        if blocking and tile in invalid_blocking_tiles:
            issues.append(
                ValidationIssue(
                    source,
                    "blocking decoration cannot overlap blocked, water, spawn, resource, or world object tiles",
                )
            )


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


def _has_adjacent_walkable_tile(
    tile: tuple[int, int],
    width: int,
    height: int,
    blocked_tiles: set[tuple[int, int]],
) -> bool:
    x, y = tile
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            candidate = (x + dx, y + dy)
            if 0 <= candidate[0] < width and 0 <= candidate[1] < height and candidate not in blocked_tiles:
                return True
    return False


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
