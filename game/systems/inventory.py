from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Inventory:
    items: dict[str, int] = field(default_factory=dict)

    def add(self, item_id: str, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.items[item_id] = self.items.get(item_id, 0) + quantity

    def remove(self, item_id: str, quantity: int = 1) -> int:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        current = self.items.get(item_id, 0)
        removed = min(current, quantity)
        remaining = current - removed
        if remaining:
            self.items[item_id] = remaining
        else:
            self.items.pop(item_id, None)
        return removed

    def count(self, item_id: str) -> int:
        return self.items.get(item_id, 0)

    def to_dict(self) -> dict[str, int]:
        return dict(self.items)

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Inventory":
        inventory = cls()
        for item_id, quantity in data.items():
            if int(quantity) > 0:
                inventory.items[item_id] = int(quantity)
        return inventory
