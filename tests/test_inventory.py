from __future__ import annotations

import unittest

from game.systems.inventory import Inventory


class InventoryTests(unittest.TestCase):
    def test_add_remove_count(self) -> None:
        inventory = Inventory()
        inventory.add("logs", 3)
        inventory.add("logs", 2)

        self.assertEqual(inventory.count("logs"), 5)
        self.assertEqual(inventory.remove("logs", 2), 2)
        self.assertEqual(inventory.count("logs"), 3)
        self.assertEqual(inventory.remove("logs", 10), 3)
        self.assertEqual(inventory.count("logs"), 0)

    def test_slot_count_uses_explicit_stackability(self) -> None:
        items = {
            "coins": {"category": "currency", "stackable": True},
            "logs": {"category": "wood", "stackable": False},
            "bronze_sword": {"category": "weapon", "stackable": False, "equip_slot": "weapon"},
            "bronze_axe": {"category": "tool", "stackable": False, "tool_for": "woodcutting"},
        }
        inventory = Inventory({"coins": 250, "logs": 2, "bronze_sword": 2, "bronze_axe": 1})

        self.assertEqual(inventory.slot_count(items), 6)
        self.assertTrue(inventory.can_add("coins", 100, item_definitions=items, slot_limit=6))
        self.assertFalse(inventory.can_add("logs", 1, item_definitions=items, slot_limit=6))


if __name__ == "__main__":
    unittest.main()
