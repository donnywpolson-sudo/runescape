from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from game.systems.inventory import COINS_ITEM_ID
from game.systems.inventory import Inventory


@dataclass(frozen=True)
class StockItem:
    item_id: str
    price: int


@dataclass(frozen=True)
class PurchaseResult:
    success: bool
    feedback: str
    item_id: str | None = None
    quantity: int = 0
    coins_spent: int = 0


class Shop:
    def __init__(
        self,
        item_definitions: dict[str, dict[str, object]],
        stock: list[dict[str, object]] | tuple[dict[str, object], ...] | None = None,
    ) -> None:
        self.item_definitions = item_definitions
        self.stock = {
            stock_item.item_id: stock_item
            for stock_item in (_stock_item_from_dict(raw_stock_item, item_definitions) for raw_stock_item in stock or [])
        }

    def stock_items(self) -> list[StockItem]:
        return sorted(self.stock.values(), key=lambda stock_item: (stock_item.price, stock_item.item_id))

    def buy(self, inventory: Inventory, item_id: str, quantity: int = 1) -> PurchaseResult:
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        stock_item = self.stock.get(item_id)
        if stock_item is None:
            return PurchaseResult(False, "Item is not for sale", item_id=item_id)
        definition = self.item_definitions.get(item_id)
        if definition is None:
            return PurchaseResult(False, "Item is unavailable", item_id=item_id)

        total_price = stock_item.price * quantity
        if inventory.count(COINS_ITEM_ID) < total_price:
            return PurchaseResult(False, f"Need {total_price} coins", item_id=item_id)

        inventory.remove(COINS_ITEM_ID, total_price)
        inventory.add(item_id, quantity)
        return PurchaseResult(
            True,
            f"Bought {quantity} {_item_name(definition, item_id)} for {total_price} coins",
            item_id=item_id,
            quantity=quantity,
            coins_spent=total_price,
        )

    def is_sellable(self, item_id: str) -> bool:
        definition = self.item_definitions.get(item_id)
        return bool(definition and int(definition.get("sell_price", 0)) > 0)

    def sell_price(self, item_id: str) -> int:
        definition = self.item_definitions.get(item_id)
        if not definition:
            return 0
        return int(definition.get("sell_price", 0))

    def sell_item(self, inventory: Inventory, item_id: str, quantity: int | None = None) -> tuple[int, int]:
        return self.sell_all(inventory, item_id, quantity)

    def sell_all(
        self,
        inventory: Inventory,
        item_id: str | None = None,
        quantity: int | None = None,
    ) -> tuple[int, int]:
        if item_id is None:
            sold = 0
            coins = 0
            for inventory_item_id in list(inventory.items):
                item_sold, item_coins = self.sell_all(inventory, inventory_item_id)
                sold += item_sold
                coins += item_coins
            return sold, coins

        amount = inventory.count(item_id)
        if quantity is not None:
            amount = min(amount, quantity)
        if amount <= 0:
            return 0, 0

        definition = self.item_definitions.get(item_id)
        if not definition:
            return 0, 0
        price = int(definition.get("sell_price", 0))
        if price <= 0:
            return 0, 0

        removed = inventory.remove(item_id, amount)
        if removed <= 0:
            return 0, 0
        return removed, removed * price


def _item_name(definition: dict[str, object], item_id: str) -> str:
    return str(definition.get("name") or item_id.replace("_", " "))


def _stock_item_from_dict(
    data: dict[str, Any],
    item_definitions: dict[str, dict[str, object]],
) -> StockItem:
    item_id = str(data["item_id"])
    raw_price = data.get("price")
    if raw_price is not None:
        return StockItem(item_id=item_id, price=int(raw_price))
    definition = item_definitions.get(item_id, {})
    buy_price = definition.get("buy_price")
    if buy_price is not None:
        return StockItem(item_id=item_id, price=int(buy_price))
    return StockItem(item_id=item_id, price=max(1, int(definition.get("sell_price", 1)) * 3))
