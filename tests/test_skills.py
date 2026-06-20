from __future__ import annotations

import unittest

from game.systems.skills import Skills, skill_xp_thresholds


DEFINITIONS = {
    "woodcutting": {
        "starting_level": 1,
        "xp_thresholds": {"1": 0, "2": 25, "3": 75},
        "actions": {"chop_tree": {"xp": 10}},
    }
}


class SkillsTests(unittest.TestCase):
    def test_skill_xp_thresholds_match_key_levels(self) -> None:
        thresholds = skill_xp_thresholds()

        self.assertEqual(thresholds["1"], 0)
        self.assertEqual(thresholds["2"], 83)
        self.assertEqual(thresholds["50"], 101333)
        self.assertEqual(thresholds["99"], 13034431)

    def test_threshold_leveling(self) -> None:
        skills = Skills(DEFINITIONS)

        skills.add_xp("woodcutting", 24)
        self.assertEqual(skills.get("woodcutting").level, 1)

        skills.add_xp("woodcutting", 1)
        self.assertEqual(skills.get("woodcutting").level, 2)

        skills.add_xp("woodcutting", 50)
        self.assertEqual(skills.get("woodcutting").level, 3)

    def test_threshold_level_calculation_caps_at_99(self) -> None:
        skills = Skills(
            {
                "cooking": {
                    "display_name": "Cooking",
                    "starting_level": 1,
                    "xp_thresholds": skill_xp_thresholds(),
                }
            }
        )

        skills.add_xp("cooking", 101333)
        self.assertEqual(skills.get("cooking").level, 50)

        skills.add_xp("cooking", 13034431 - 101333)
        self.assertEqual(skills.get("cooking").level, 99)

        skills.add_xp("cooking", 1_000_000)
        self.assertEqual(skills.get("cooking").level, 99)

    def test_starting_level_is_floor_when_xp_changes(self) -> None:
        skills = Skills(
            {
                "hitpoints": {
                    "display_name": "Hitpoints",
                    "starting_level": 10,
                    "xp_thresholds": skill_xp_thresholds(),
                }
            }
        )

        skills.add_xp("hitpoints", 1)

        self.assertEqual(skills.get("hitpoints").level, 10)

    def test_old_save_missing_cooking_loads_with_cooking_level_one(self) -> None:
        skills = Skills(
            {
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
            }
        )

        skills.load_dict({"woodcutting": {"xp": 83, "level": 2}})

        self.assertEqual(skills.get("woodcutting").level, 2)
        self.assertEqual(skills.get("cooking").level, 1)
        self.assertEqual(skills.get("cooking").xp, 0)


if __name__ == "__main__":
    unittest.main()
