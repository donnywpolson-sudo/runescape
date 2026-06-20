from __future__ import annotations

from game.systems.inventory import Inventory


class Shop:
    def __init__(self, item_definitions: dict[str, dict[str, object]]) -> None:
        self.item_definitions = item_definitions

    def sell_all(self, inventory: Inventory, item_id: str) -> tuple[int, int]:
        quantity = inventory.count(item_id)
        if quantity <= 0:
            return 0, 0

        price = int(self.item_definitions[item_id].get("sell_price", 0))
        removed = inventory.remove(item_id, quantity)
        if removed <= 0:
            return 0, 0
        return removed, removed * price
