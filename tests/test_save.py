from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from game.engine.save import create_default_save, get_save_path, load_game, save_game


class SaveTests(unittest.TestCase):
    def test_save_round_trip(self) -> None:
        state = {
            "player": {"tile": [15, 15], "position": [15.5, 15.5]},
            "inventory": {"logs": 2, "copper_ore": 1, "raw_fish": 3},
            "coins": 6,
            "skills": {
                "woodcutting": {"level": 2, "xp": 100},
                "mining": {"level": 1, "xp": 20},
                "fishing": {"level": 1, "xp": 15},
            },
            "world": {
                "resource_nodes": {
                    "tree_01": {"depleted": True, "respawn_at": 123.0}
                }
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
            state["coins"] = 125
            state["inventory"]["bronze_axe"] = 1
            state["world"]["chopped_trees"].append("lumbridge_tree_1")

            save_game("alice", state, save_dir)

            self.assertEqual(load_game("alice", save_dir), state)

    def test_default_save_includes_empty_bank(self) -> None:
        state = create_default_save("alice")

        self.assertEqual(state["bank"], {})

    def test_two_users_do_not_overwrite_each_other(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory) / "saves"
            alice_state = create_default_save("alice")
            bob_state = create_default_save("bob")
            alice_state["coins"] = 50
            bob_state["coins"] = 300

            alice_path = save_game("alice", alice_state, save_dir)
            bob_path = save_game("bob", bob_state, save_dir)

            self.assertNotEqual(alice_path, bob_path)
            self.assertEqual(load_game("alice", save_dir)["coins"], 50)
            self.assertEqual(load_game("bob", save_dir)["coins"], 300)


if __name__ == "__main__":
    unittest.main()
