from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from json import JSONDecodeError
import logging
import os
from pathlib import Path
import re
from typing import Any

from game import settings
from game.systems.inventory import COINS_ITEM_ID

DEFAULT_SAVE_DIR = settings.SAVES_DIR
SAVE_VERSION = 3
MAX_SAVE_STEM_LENGTH = 64
LOGGER = logging.getLogger(__name__)
STARTER_ITEMS = {
    "bronze_axe": 1,
    "bronze_pickaxe": 1,
    "fishing_rod": 1,
    "bronze_sword": 1,
    "bronze_shield": 1,
}
DEFAULT_SKILL_IDS = (
    "woodcutting",
    "mining",
    "fishing",
    "cooking",
    "attack",
    "strength",
    "defence",
    "hitpoints",
    "smithing",
)
_SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def get_save_path(username: str, save_dir: str | Path = DEFAULT_SAVE_DIR) -> Path:
    save_root = Path(save_dir)
    save_root.mkdir(parents=True, exist_ok=True)
    return save_root / f"{sanitize_username_for_filename(username)}.json"


def sanitize_username_for_filename(username: str) -> str:
    raw_username = username.strip()
    if not raw_username:
        raise ValueError("Username is required")

    sanitized = _SAFE_FILENAME_PATTERN.sub("_", raw_username)
    sanitized = sanitized.strip(" ._")
    sanitized = sanitized[:MAX_SAVE_STEM_LENGTH].strip(" ._")
    if not sanitized:
        sanitized = "user"

    is_reserved = sanitized.upper() in _WINDOWS_RESERVED_NAMES
    changed = sanitized != raw_username
    if changed or is_reserved:
        digest = hashlib.sha256(raw_username.encode("utf-8")).hexdigest()[:12]
        available_length = MAX_SAVE_STEM_LENGTH - len(digest) - 1
        sanitized = f"{sanitized[:available_length].strip(' ._')}_{digest}"

    return sanitized


def create_default_save(username: str) -> dict[str, Any]:
    username = username.strip()
    if not username:
        raise ValueError("Username is required")

    return deepcopy(
        {
            "version": SAVE_VERSION,
            "username": username,
            "player": {
                "tile": [15, 15],
                "position": [15.5, 15.5],
            },
            "camera": {
                "center_x": 15.0,
                "center_y": 15.0,
                "heading": 45.0,
                "zoom": 22.0,
            },
            "inventory": dict(STARTER_ITEMS),
            "bank": {},
            "equipment": {},
            "skills": {
                skill_id: {"xp": 0, "level": 10 if skill_id == "hitpoints" else 1}
                for skill_id in DEFAULT_SKILL_IDS
            },
            "combat": {
                "current_hitpoints": 10,
                "mobs": {},
                "ground_items": [],
            },
            "quest_state": {},
            "depleted_resources": [],
            "chopped_trees": [],
            "world": {
                "depleted_resources": [],
                "chopped_trees": [],
                "resource_nodes": {},
                "combat": {
                    "current_hitpoints": 10,
                    "mobs": {},
                    "ground_items": [],
                },
                "quest_state": {},
                "day": 1,
                "minute": 360.0,
            },
            "time": {"day": 1, "minute": 360.0},
        }
    )


def save_game(
    username_or_path: str | Path,
    state: dict[str, Any],
    save_dir: str | Path = DEFAULT_SAVE_DIR,
) -> Path:
    if isinstance(username_or_path, Path):
        path = username_or_path
        _write_json(path, state)
        return path

    username = username_or_path
    path = get_save_path(username, save_dir)
    state_to_save = deepcopy(state)
    state_to_save["username"] = username
    _write_json(path, state_to_save)
    return path


def load_game(
    username_or_path: str | Path,
    save_dir: str | Path = DEFAULT_SAVE_DIR,
) -> dict[str, Any] | None:
    path = (
        username_or_path
        if isinstance(username_or_path, Path)
        else get_save_path(username_or_path, save_dir)
    )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, JSONDecodeError) as exc:
        LOGGER.warning("Could not load save %s: %s", path, exc)
        backup_data = _load_backup(path)
        if backup_data is not None:
            return backup_data
        return None

    if not isinstance(data, dict):
        LOGGER.warning("Save %s did not contain a JSON object", path)
        return None
    return data


def load_or_create_save(
    username: str,
    save_dir: str | Path = DEFAULT_SAVE_DIR,
) -> tuple[dict[str, Any], bool]:
    state = load_game(username, save_dir)
    if state is not None:
        return state, False

    state = create_default_save(username)
    save_game(username, state, save_dir)
    return state, True


def migrate_legacy_coins_to_inventory(state: dict[str, Any]) -> dict[str, Any]:
    migrated = deepcopy(state)
    inventory = migrated.get("inventory")
    inventory = dict(inventory) if isinstance(inventory, dict) else {}

    legacy_coins = _positive_int(migrated.pop("coins", 0))
    inventory_coins = _positive_int(inventory.get(COINS_ITEM_ID, 0))
    if legacy_coins > 0 and inventory_coins <= 0:
        inventory[COINS_ITEM_ID] = legacy_coins
    elif inventory_coins <= 0:
        inventory.pop(COINS_ITEM_ID, None)

    migrated["inventory"] = inventory
    return migrated


def migrate_legacy_starter_items(state: dict[str, Any]) -> dict[str, Any]:
    migrated = deepcopy(state)
    version = _positive_int(migrated.get("version", 1))
    if version >= 2:
        return migrated

    inventory = migrated.get("inventory")
    inventory = dict(inventory) if isinstance(inventory, dict) else {}
    equipment = migrated.get("equipment")
    equipped_items = set(equipment.values()) if isinstance(equipment, dict) else set()
    for item_id, quantity in STARTER_ITEMS.items():
        if _positive_int(inventory.get(item_id, 0)) <= 0 and item_id not in equipped_items:
            inventory[item_id] = quantity
    migrated["inventory"] = inventory
    migrated.setdefault("equipment", {})
    return migrated


def migrate_save_state(state: dict[str, Any]) -> dict[str, Any]:
    migrated = migrate_legacy_coins_to_inventory(state)
    migrated = migrate_legacy_starter_items(migrated)
    migrated = migrate_playable_v1_defaults(migrated)
    return migrated


def migrate_playable_v1_defaults(state: dict[str, Any]) -> dict[str, Any]:
    migrated = deepcopy(state)
    skills = migrated.get("skills")
    skills = dict(skills) if isinstance(skills, dict) else {}
    for skill_id in DEFAULT_SKILL_IDS:
        default_level = 10 if skill_id == "hitpoints" else 1
        values = skills.get(skill_id)
        if isinstance(values, dict):
            values = dict(values)
            values.setdefault("xp", 0)
            values.setdefault("level", default_level)
            skills[skill_id] = values
        else:
            skills[skill_id] = {"xp": 0, "level": default_level}
    migrated["skills"] = skills

    combat = migrated.get("combat")
    combat = dict(combat) if isinstance(combat, dict) else {}
    combat.setdefault("current_hitpoints", skills["hitpoints"]["level"])
    combat.setdefault("mobs", {})
    combat.setdefault("ground_items", [])
    migrated["combat"] = combat

    world = migrated.get("world")
    world = dict(world) if isinstance(world, dict) else {}
    world_combat = world.get("combat")
    world_combat = dict(world_combat) if isinstance(world_combat, dict) else {}
    world_combat.setdefault("current_hitpoints", combat["current_hitpoints"])
    world_combat.setdefault("mobs", {})
    world_combat.setdefault("ground_items", [])
    world["combat"] = world_combat
    world.setdefault("quest_state", migrated.get("quest_state", {}))
    migrated["world"] = world

    migrated.setdefault("quest_state", world.get("quest_state", {}))
    migrated["version"] = SAVE_VERSION
    return migrated


def _write_json(path: Path, state: dict[str, Any]) -> None:
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        _backup_path(path).write_bytes(path.read_bytes())

    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def _positive_int(value: object) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return 0
    return max(quantity, 0)


def _backup_path(path: Path) -> Path:
    return path.with_suffix(f"{path.suffix}.bak")


def _load_backup(path: Path) -> dict[str, Any] | None:
    backup_path = _backup_path(path)
    try:
        data = json.loads(backup_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, JSONDecodeError):
        return None
    if isinstance(data, dict):
        LOGGER.info("Loaded backup save %s", backup_path)
        return data
    return None
