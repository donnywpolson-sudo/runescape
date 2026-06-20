from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from game.engine.save import (
    create_default_save,
    get_save_path,
    load_game,
    migrate_legacy_coins_to_inventory,
    save_game,
)


class SaveTests(unittest.TestCase):
    def test_save_round_trip(self) -> None:
        state = {
            "player": {"tile": [15, 15], "position": [15.5, 15.5]},
            "inventory": {"logs": 2, "copper_ore": 1, "raw_fish": 3, "coins": 6},
            "skills": {
                "woodcutting": {"level": 2, "xp": 100},
                "mining": {"level": 1, "xp": 20},
                "fishing": {"level": 1, "xp": 15},
                "cooking": {"level": 1, "xp": 0},
            },
            "world": {
                "resource_nodes": {
                    "tree_01": {"depleted": True, "respawn_at": 123.0}
                },
                "combat": {
                    "mobs": {"mob_01": {"hitpoints": 0, "dead": True, "respawn_at": 222.0}},
                    "ground_items": [
                        {"object_id": "ground_item_0001", "item_id": "coins", "quantity": 3, "tile": [2, 2]}
                    ],
                },
            },
            "combat": {
                "mobs": {"mob_01": {"hitpoints": 0, "dead": True, "respawn_at": 222.0}},
                "ground_items": [
                    {"object_id": "ground_item_0001", "item_id": "coins", "quantity": 3, "tile": [2, 2]}
                ],
            },
            "time": {"day": 2, "minute": 480},
            "camera": {"center_x": 12, "center_y": 11, "heading": 45, "zoom": 20},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            save_game(path, state)

            self.assertEqual(load_game(path), state)

    def test_missing_or_corrupt_save_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            self.assertIsNone(load_game(missing))

            corrupt = Path(directory) / "savegame.json"
            corrupt.write_text("{not valid json", encoding="utf-8")
            self.assertIsNone(load_game(corrupt))

    def test_backup_created_before_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            first = {"coins": 1}
            second = {"coins": 2}

            save_game(path, first)
            save_game(path, second)

            self.assertEqual(load_game(path), second)
            self.assertEqual(load_game(path.with_suffix(".json.bak")), first)

    def test_creating_per_user_save_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory) / "saves"

            path = get_save_path("alice", save_dir)

            self.assertEqual(path, save_dir / "alice.json")
            self.assertTrue(save_dir.exists())

    def test_sanitized_username_save_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory) / "saves"

            path = get_save_path("../A lice?", save_dir)

            self.assertEqual(path.parent, save_dir)
            self.assertEqual(path.suffix, ".json")
            self.assertNotIn("..", path.name)
            self.assertNotIn("/", path.name)
            self.assertNotIn("\\", path.name)

    def test_account_save_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory) / "saves"
            state = create_default_save("alice")
            state["inventory"]["coins"] = 125
            state["inventory"]["bronze_axe"] = 1
            state["world"]["chopped_trees"].append("lumbridge_tree_1")

            save_game("alice", state, save_dir)

            self.assertEqual(load_game("alice", save_dir), state)

    def test_default_save_includes_empty_bank(self) -> None:
        state = create_default_save("alice")

        self.assertEqual(state["bank"], {})

    def test_default_save_includes_empty_combat_state(self) -> None:
        state = create_default_save("alice")

        self.assertEqual(state["combat"], {"current_hitpoints": 10, "mobs": {}, "ground_items": []})
        self.assertEqual(state["world"]["combat"], {"current_hitpoints": 10, "mobs": {}, "ground_items": []})
        self.assertEqual(state["quest_state"], {})

    def test_default_save_includes_skilling_and_combat_skills(self) -> None:
        state = create_default_save("alice")

        self.assertEqual(state["skills"]["cooking"], {"xp": 0, "level": 1})
        self.assertEqual(state["skills"]["attack"], {"xp": 0, "level": 1})
        self.assertEqual(state["skills"]["strength"], {"xp": 0, "level": 1})
        self.assertEqual(state["skills"]["defence"], {"xp": 0, "level": 1})
        self.assertEqual(state["skills"]["hitpoints"], {"xp": 0, "level": 10})
        self.assertEqual(state["skills"]["smithing"], {"xp": 0, "level": 1})
        self.assertNotIn("coins", state)

    def test_default_save_includes_starter_tools_and_equipment_slots(self) -> None:
        state = create_default_save("alice")

        self.assertEqual(state["inventory"]["bronze_axe"], 1)
        self.assertEqual(state["inventory"]["bronze_pickaxe"], 1)
        self.assertEqual(state["inventory"]["fishing_rod"], 1)
        self.assertEqual(state["inventory"]["bronze_sword"], 1)
        self.assertEqual(state["inventory"]["bronze_shield"], 1)
        self.assertEqual(state["equipment"], {})

    def test_two_users_do_not_overwrite_each_other(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory) / "saves"
            alice_state = create_default_save("alice")
            bob_state = create_default_save("bob")
            alice_state["inventory"]["coins"] = 50
            bob_state["inventory"]["coins"] = 300

            alice_path = save_game("alice", alice_state, save_dir)
            bob_path = save_game("bob", bob_state, save_dir)

            self.assertNotEqual(alice_path, bob_path)
            self.assertEqual(load_game("alice", save_dir)["inventory"]["coins"], 50)
            self.assertEqual(load_game("bob", save_dir)["inventory"]["coins"], 300)

    def test_legacy_top_level_coins_migrate_to_inventory_item(self) -> None:
        state = {
            "inventory": {"logs": 2},
            "coins": 125,
        }

        migrated = migrate_legacy_coins_to_inventory(state)

        self.assertEqual(migrated["inventory"], {"logs": 2, "coins": 125})
        self.assertNotIn("coins", migrated)

    def test_legacy_coin_migration_does_not_double_count_inventory_coins(self) -> None:
        state = {
            "inventory": {"coins": 25},
            "coins": 125,
        }

        migrated = migrate_legacy_coins_to_inventory(state)

        self.assertEqual(migrated["inventory"], {"coins": 25})
        self.assertNotIn("coins", migrated)


if __name__ == "__main__":
    unittest.main()
