from __future__ import annotations

from game.systems.inventory import Inventory


class Shop:
    def __init__(self, item_definitions: dict[str, dict[str, object]]) -> None:
        self.item_definitions = item_definitions

    def sell_all(self, inventory: Inventory, item_id: str | None = None) -> tuple[int, int]:
        if item_id is None:
            sold = 0
            coins = 0
            for inventory_item_id in list(inventory.items):
                item_sold, item_coins = self.sell_all(inventory, inventory_item_id)
                sold += item_sold
                coins += item_coins
            return sold, coins

        quantity = inventory.count(item_id)
        if quantity <= 0:
            return 0, 0

        definition = self.item_definitions.get(item_id)
        if not definition:
            return 0, 0
        price = int(definition.get("sell_price", 0))
        if price <= 0:
            return 0, 0

        removed = inventory.remove(item_id, quantity)
        if removed <= 0:
            return 0, 0
        return removed, removed * price
