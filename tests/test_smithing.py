from __future__ import annotations

from game.systems.inventory import Inventory
from game.systems.skills import Skills, osrs_xp_thresholds
from game.systems.smithing import SmithingSystem


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_smelting_completes_after_timer_and_grants_bar_and_xp() -> None:
    clock = FakeClock()
    inventory = Inventory({"copper_ore": 1, "tin_ore": 1})
    skills = Skills(_skills())
    smithing = SmithingSystem(_recipes(), inventory, skills, time_provider=clock)

    started = smithing.start_smelting("copper_ore")

    assert started.success
    assert started.pending
    assert started.feedback == "Smelting Bronze bar... 1.8s"
    assert inventory.to_dict() == {"copper_ore": 1, "tin_ore": 1}

    clock.now += started.duration
    completed = smithing.update()

    assert completed is not None
    assert completed.success
    assert inventory.to_dict() == {"bronze_bar": 1}
    assert skills.xp("smithing") == 6


def test_smithing_requires_ingredients_and_level() -> None:
    inventory = Inventory({"iron_bar": 1})
    skills = Skills(_skills())
    smithing = SmithingSystem(_recipes(), inventory, skills)

    blocked = smithing.start_smithing("iron_bar")

    assert not blocked.success
    assert blocked.feedback == "You need Smithing level 15"

    skills.add_xp("smithing", osrs_xp_thresholds()["15"])
    started = smithing.start_smithing("iron_bar")

    assert started.success


def test_pending_smithing_can_be_cancelled() -> None:
    clock = FakeClock()
    inventory = Inventory({"bronze_bar": 1})
    skills = Skills(_skills())
    smithing = SmithingSystem(_recipes(), inventory, skills, time_provider=clock)

    smithing.start_smithing("bronze_bar")

    assert smithing.cancel_pending()
    clock.now += 10
    assert smithing.update() is None
    assert inventory.to_dict() == {"bronze_bar": 1}


def _skills() -> dict[str, dict[str, object]]:
    return {
        "smithing": {
            "display_name": "Smithing",
            "starting_level": 1,
            "xp_thresholds": osrs_xp_thresholds(),
        }
    }


def _recipes() -> dict[str, object]:
    return {
        "smelting": [
            {
                "recipe_id": "bronze_bar",
                "display_name": "Bronze bar",
                "inputs": {"copper_ore": 1, "tin_ore": 1},
                "output_item_id": "bronze_bar",
                "output_quantity": 1,
                "required_level": 1,
                "xp_reward": 6,
                "base_seconds": 1.8,
            }
        ],
        "smithing": [
            {
                "recipe_id": "bronze_sword",
                "display_name": "Bronze sword",
                "inputs": {"bronze_bar": 1},
                "output_item_id": "bronze_sword",
                "output_quantity": 1,
                "required_level": 1,
                "xp_reward": 12,
                "base_seconds": 2.0,
            },
            {
                "recipe_id": "iron_sword",
                "display_name": "Iron sword",
                "inputs": {"iron_bar": 1},
                "output_item_id": "iron_sword",
                "output_quantity": 1,
                "required_level": 15,
                "xp_reward": 25,
                "base_seconds": 2.4,
            },
        ],
    }
