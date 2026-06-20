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


if __name__ == "__main__":
    unittest.main()
