from __future__ import annotations

from game.systems.inventory import Inventory
from game.systems.shop import Shop


def test_shop_sells_all_sellable_inventory_items() -> None:
    inventory = Inventory({"logs": 2, "raw_shrimp": 3, "cooked_shrimp": 1, "unknown_item": 5})
    shop = Shop(
        {
            "logs": {"sell_price": 3},
            "raw_shrimp": {"sell_price": 4},
            "cooked_shrimp": {"sell_price": 7},
            "unknown_item": {"sell_price": 0},
        }
    )

    sold, coins = shop.sell_all(inventory)

    assert sold == 6
    assert coins == 25
    assert inventory.to_dict() == {"unknown_item": 5}


def test_shop_can_still_sell_one_item_type() -> None:
    inventory = Inventory({"logs": 2, "raw_shrimp": 3})
    shop = Shop({"logs": {"sell_price": 3}, "raw_shrimp": {"sell_price": 4}})

    sold, coins = shop.sell_all(inventory, "logs")

    assert sold == 2
    assert coins == 6
    assert inventory.to_dict() == {"raw_shrimp": 3}


def test_shop_can_sell_limited_quantity() -> None:
    inventory = Inventory({"logs": 5})
    shop = Shop({"logs": {"sell_price": 3}})

    sold, coins = shop.sell_item(inventory, "logs", 2)

    assert sold == 2
    assert coins == 6
    assert inventory.to_dict() == {"logs": 3}


def test_shop_buy_adds_stock_item_and_spends_coins() -> None:
    inventory = Inventory({"coins": 30})
    shop = Shop(
        {
            "coins": {"name": "Coins", "sell_price": 0},
            "bronze_axe": {"name": "Bronze axe", "sell_price": 8},
        },
        [{"item_id": "bronze_axe", "price": 25}],
    )

    result = shop.buy(inventory, "bronze_axe")

    assert result.success is True
    assert result.coins_spent == 25
    assert inventory.to_dict() == {"coins": 5, "bronze_axe": 1}


def test_shop_buy_supports_limited_quantity() -> None:
    inventory = Inventory({"coins": 80})
    shop = Shop(
        {
            "coins": {"name": "Coins", "sell_price": 0},
            "bronze_axe": {"name": "Bronze axe", "sell_price": 8},
        },
        [{"item_id": "bronze_axe", "price": 25}],
    )

    result = shop.buy(inventory, "bronze_axe", 3)

    assert result.success is True
    assert result.coins_spent == 75
    assert result.quantity == 3
    assert inventory.to_dict() == {"coins": 5, "bronze_axe": 3}


def test_shop_buy_requires_enough_coins() -> None:
    inventory = Inventory({"coins": 10})
    shop = Shop(
        {"coins": {"name": "Coins", "sell_price": 0}, "bronze_axe": {"name": "Bronze axe", "sell_price": 8}},
        [{"item_id": "bronze_axe", "price": 25}],
    )

    result = shop.buy(inventory, "bronze_axe")

    assert result.success is False
    assert inventory.to_dict() == {"coins": 10}


def test_shop_buy_rejects_items_not_in_stock() -> None:
    inventory = Inventory({"coins": 50})
    shop = Shop({"coins": {"name": "Coins", "sell_price": 0}, "bronze_axe": {"name": "Bronze axe", "sell_price": 8}})

    result = shop.buy(inventory, "bronze_axe")

    assert result.success is False
    assert inventory.to_dict() == {"coins": 50}
