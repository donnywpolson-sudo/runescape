from __future__ import annotations

import pytest

from game.systems.bank import Bank
from game.systems.inventory import Inventory


def test_deposit_stack_moves_items_from_inventory_to_bank() -> None:
    inventory = Inventory({"logs": 5})
    bank = Bank()

    deposited = bank.deposit(inventory, "logs", 3)

    assert deposited == 3
    assert inventory.count("logs") == 2
    assert bank.count("logs") == 3


def test_deposit_all_moves_every_inventory_stack() -> None:
    inventory = Inventory({"logs": 2, "copper_ore": 4})
    bank = Bank({"raw_fish": 1})

    deposited = bank.deposit_all(inventory)

    assert deposited == {"logs": 2, "copper_ore": 4}
    assert inventory.to_dict() == {}
    assert bank.to_dict() == {"raw_fish": 1, "logs": 2, "copper_ore": 4}


def test_withdraw_stack_moves_items_from_bank_to_inventory() -> None:
    inventory = Inventory()
    bank = Bank({"raw_fish": 5})

    withdrawn = bank.withdraw(inventory, "raw_fish", 2)

    assert withdrawn == 2
    assert inventory.count("raw_fish") == 2
    assert bank.count("raw_fish") == 3


def test_bank_serialization_round_trip() -> None:
    bank = Bank.from_dict({"logs": 2, "raw_fish": 0})

    assert bank.to_dict() == {"logs": 2}


def test_missing_bank_save_data_loads_as_empty_bank() -> None:
    assert Bank.from_dict(None).to_dict() == {}


@pytest.mark.parametrize("operation", ["deposit", "withdraw"])
def test_invalid_quantities_are_rejected(operation: str) -> None:
    inventory = Inventory({"logs": 1})
    bank = Bank({"logs": 1})

    with pytest.raises(ValueError):
        if operation == "deposit":
            bank.deposit(inventory, "logs", 0)
        else:
            bank.withdraw(inventory, "logs", 0)
