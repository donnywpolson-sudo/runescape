from __future__ import annotations

from dataclasses import dataclass, field


COINS_ITEM_ID = "coins"
INVENTORY_SLOT_LIMIT = 28


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

    def slot_count(self, item_definitions: dict[str, dict[str, object]] | None = None) -> int:
        return inventory_slot_count(self.items, item_definitions or {})

    def can_add(
        self,
        item_id: str,
        quantity: int = 1,
        *,
        item_definitions: dict[str, dict[str, object]] | None = None,
        slot_limit: int = INVENTORY_SLOT_LIMIT,
    ) -> bool:
        return inventory_can_add(
            self.items,
            item_definitions or {},
            item_id,
            quantity,
            slot_limit=slot_limit,
        )

    def can_transact(
        self,
        *,
        item_definitions: dict[str, dict[str, object]] | None = None,
        remove: dict[str, int] | None = None,
        add: dict[str, int] | None = None,
        slot_limit: int = INVENTORY_SLOT_LIMIT,
    ) -> bool:
        return inventory_can_transact(
            self.items,
            item_definitions or {},
            remove=remove,
            add=add,
            slot_limit=slot_limit,
        )

    def to_dict(self) -> dict[str, int]:
        return dict(self.items)

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Inventory":
        inventory = cls()
        for item_id, quantity in data.items():
            if int(quantity) > 0:
                inventory.items[item_id] = int(quantity)
        return inventory


def inventory_slot_count(
    items: dict[str, int],
    item_definitions: dict[str, dict[str, object]] | None = None,
) -> int:
    definitions = item_definitions or {}
    slots = 0
    for item_id, quantity in items.items():
        quantity = int(quantity)
        if quantity <= 0:
            continue
        if is_non_stackable_item(definitions, item_id):
            slots += quantity
        else:
            slots += 1
    return slots


def inventory_can_add(
    items: dict[str, int],
    item_definitions: dict[str, dict[str, object]] | None,
    item_id: str,
    quantity: int = 1,
    *,
    slot_limit: int = INVENTORY_SLOT_LIMIT,
) -> bool:
    if quantity <= 0:
        return True
    definitions = item_definitions or {}
    current = {
        existing_item_id: int(existing_quantity)
        for existing_item_id, existing_quantity in items.items()
        if int(existing_quantity) > 0
    }
    current[item_id] = current.get(item_id, 0) + int(quantity)
    return inventory_slot_count(current, definitions) <= slot_limit


def inventory_can_transact(
    items: dict[str, int],
    item_definitions: dict[str, dict[str, object]] | None,
    *,
    remove: dict[str, int] | None = None,
    add: dict[str, int] | None = None,
    slot_limit: int = INVENTORY_SLOT_LIMIT,
) -> bool:
    current = {
        item_id: int(quantity)
        for item_id, quantity in items.items()
        if int(quantity) > 0
    }
    for item_id, quantity in (remove or {}).items():
        if quantity <= 0:
            continue
        remaining = current.get(item_id, 0) - int(quantity)
        if remaining > 0:
            current[item_id] = remaining
        else:
            current.pop(item_id, None)
    for item_id, quantity in (add or {}).items():
        if quantity <= 0:
            continue
        current[item_id] = current.get(item_id, 0) + int(quantity)
    return inventory_slot_count(current, item_definitions or {}) <= slot_limit


def is_stackable_item(
    item_definitions: dict[str, dict[str, object]] | None,
    item_id: str,
) -> bool:
    definition = (item_definitions or {}).get(item_id, {})
    if "stackable" in definition:
        return bool(definition.get("stackable"))
    if item_id == COINS_ITEM_ID:
        return True
    return False


def is_non_stackable_item(
    item_definitions: dict[str, dict[str, object]] | None,
    item_id: str,
) -> bool:
    return not is_stackable_item(item_definitions, item_id)
