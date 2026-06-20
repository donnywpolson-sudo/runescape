from __future__ import annotations

from game.systems.inventory import Inventory
from game.systems.shop import Shop


def test_shop_sells_all_sellable_inventory_items() -> None:
    inventory = Inventory({"logs": 2, "raw_shrimp": 3, "unknown_item": 5})
    shop = Shop(
        {
            "logs": {"sell_price": 3},
            "raw_shrimp": {"sell_price": 4},
            "unknown_item": {"sell_price": 0},
        }
    )

    sold, coins = shop.sell_all(inventory)

    assert sold == 5
    assert coins == 18
    assert inventory.to_dict() == {"unknown_item": 5}


def test_shop_can_still_sell_one_item_type() -> None:
    inventory = Inventory({"logs": 2, "raw_shrimp": 3})
    shop = Shop({"logs": {"sell_price": 3}, "raw_shrimp": {"sell_price": 4}})

    sold, coins = shop.sell_all(inventory, "logs")

    assert sold == 2
    assert coins == 6
    assert inventory.to_dict() == {"raw_shrimp": 3}
