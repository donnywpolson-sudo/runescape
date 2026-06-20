from __future__ import annotations

import unittest

from game.systems.skills import Skills


DEFINITIONS = {
    "woodcutting": {
        "starting_level": 1,
        "xp_thresholds": {"1": 0, "2": 25, "3": 75},
        "actions": {"chop_tree": {"xp": 10}},
    }
}


class SkillsTests(unittest.TestCase):
    def test_threshold_leveling(self) -> None:
        skills = Skills(DEFINITIONS)

        skills.add_xp("woodcutting", 24)
        self.assertEqual(skills.get("woodcutting").level, 1)

        skills.add_xp("woodcutting", 1)
        self.assertEqual(skills.get("woodcutting").level, 2)

        skills.add_xp("woodcutting", 50)
        self.assertEqual(skills.get("woodcutting").level, 3)


if __name__ == "__main__":
    unittest.main()
