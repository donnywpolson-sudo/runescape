from __future__ import annotations

from dataclasses import dataclass, field

from game.systems.inventory import INVENTORY_SLOT_LIMIT, Inventory, inventory_can_add


@dataclass
class Bank:
    items: dict[str, int] = field(default_factory=dict)
    item_definitions: dict[str, dict[str, object]] = field(default_factory=dict)
    slot_limit: int = INVENTORY_SLOT_LIMIT

    def deposit(self, inventory: Inventory, item_id: str, quantity: int | None = None) -> int:
        if quantity is None:
            amount = inventory.count(item_id)
            if amount <= 0:
                return 0
        else:
            amount = quantity
        _validate_quantity(amount)
        removed = inventory.remove(item_id, amount)
        if removed:
            self.items[item_id] = self.items.get(item_id, 0) + removed
        return removed

    def deposit_all(self, inventory: Inventory) -> dict[str, int]:
        deposited: dict[str, int] = {}
        for item_id, quantity in list(inventory.items.items()):
            if quantity <= 0:
                continue
            removed = self.deposit(inventory, item_id, quantity)
            if removed:
                deposited[item_id] = removed
        return deposited

    def withdraw(self, inventory: Inventory, item_id: str, quantity: int | None = None) -> int:
        if quantity is None:
            amount = self.count(item_id)
            if amount <= 0:
                return 0
        else:
            amount = quantity
        _validate_quantity(amount)
        current = self.count(item_id)
        removed = min(current, amount)
        while removed > 0 and not inventory_can_add(
            inventory.to_dict(),
            self.item_definitions,
            item_id,
            removed,
            slot_limit=self.slot_limit,
        ):
            removed -= 1
        if not removed:
            return 0

        remaining = current - removed
        if remaining:
            self.items[item_id] = remaining
        else:
            self.items.pop(item_id, None)
        inventory.add(item_id, removed)
        return removed

    def count(self, item_id: str) -> int:
        return self.items.get(item_id, 0)

    def to_dict(self) -> dict[str, int]:
        return dict(self.items)

    @classmethod
    def from_dict(cls, data: dict[str, int] | None) -> "Bank":
        bank = cls()
        if not isinstance(data, dict):
            return bank
        for item_id, quantity in data.items():
            if int(quantity) > 0:
                bank.items[str(item_id)] = int(quantity)
        return bank


def _validate_quantity(quantity: int) -> None:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
