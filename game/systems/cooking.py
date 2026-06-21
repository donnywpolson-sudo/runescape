from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

from game.systems.inventory import inventory_can_transact


TimeProvider = Callable[[], float]


@dataclass(frozen=True)
class CookingRecipe:
    raw_item_id: str
    cooked_item_id: str
    required_level: int
    xp_reward: int
    base_cook_seconds: float


@dataclass(frozen=True)
class CookingResult:
    success: bool
    feedback: str
    raw_item_id: str | None = None
    cooked_item_id: str | None = None
    xp: int = 0
    pending: bool = False
    duration: float = 0.0


@dataclass(frozen=True)
class PendingCook:
    raw_item_id: str
    complete_at: float
    duration: float


class CookingSystem:
    def __init__(
        self,
        item_definitions: dict[str, dict[str, object]],
        inventory: Any,
        skills: Any,
        *,
        time_provider: TimeProvider = time.time,
    ) -> None:
        self.item_definitions = item_definitions
        self.inventory = inventory
        self.skills = skills
        self.time_provider = time_provider
        self.recipes = _recipes_from_items(item_definitions)
        self.pending: PendingCook | None = None

    def is_cookable(self, item_id: str) -> bool:
        return item_id in self.recipes

    def start_cooking(self, raw_item_id: str | None) -> CookingResult:
        if raw_item_id is None or raw_item_id not in self.recipes:
            return CookingResult(False, "Select a raw fish first")

        recipe = self.recipes[raw_item_id]
        if self.pending is not None:
            if self.pending.raw_item_id == raw_item_id:
                return CookingResult(
                    True,
                    _pending_feedback(self.item_definitions, raw_item_id, self.remaining_seconds()),
                    raw_item_id=raw_item_id,
                    cooked_item_id=recipe.cooked_item_id,
                    pending=True,
                    duration=self.pending.duration,
                )
            self.cancel_pending()

        if self.inventory.count(raw_item_id) <= 0:
            return CookingResult(False, f"No {_item_name(self.item_definitions, raw_item_id)} to cook")

        current_level = _skill_level(self.skills, "cooking")
        if current_level < recipe.required_level:
            return CookingResult(False, f"You need Cooking level {recipe.required_level}")
        if not inventory_can_transact(
            self.inventory.to_dict(),
            self.item_definitions,
            remove={recipe.raw_item_id: 1},
            add={recipe.cooked_item_id: 1},
        ):
            return CookingResult(False, "Inventory is full")

        duration = self.cook_duration(recipe)
        self.pending = PendingCook(
            raw_item_id=raw_item_id,
            complete_at=self.time_provider() + duration,
            duration=duration,
        )
        return CookingResult(
            True,
            _start_feedback(self.item_definitions, raw_item_id, duration),
            raw_item_id=raw_item_id,
            cooked_item_id=recipe.cooked_item_id,
            pending=True,
            duration=duration,
        )

    def update(self) -> CookingResult | None:
        if self.pending is None or self.time_provider() < self.pending.complete_at:
            return None

        pending = self.pending
        self.pending = None
        recipe = self.recipes.get(pending.raw_item_id)
        if recipe is None:
            return CookingResult(False, "Select a raw fish first")
        if not inventory_can_transact(
            self.inventory.to_dict(),
            self.item_definitions,
            remove={recipe.raw_item_id: 1},
            add={recipe.cooked_item_id: 1},
        ):
            return CookingResult(False, "Inventory is full")

        if self.inventory.remove(recipe.raw_item_id, 1) != 1:
            return CookingResult(False, f"No {_item_name(self.item_definitions, recipe.raw_item_id)} to cook")

        self.inventory.add(recipe.cooked_item_id, 1)
        self.skills.add_xp("cooking", recipe.xp_reward)
        return CookingResult(
            True,
            _success_feedback(self.item_definitions, self.skills, recipe),
            raw_item_id=recipe.raw_item_id,
            cooked_item_id=recipe.cooked_item_id,
            xp=recipe.xp_reward,
        )

    def cancel_pending(self) -> bool:
        if self.pending is None:
            return False
        self.pending = None
        return True

    def remaining_seconds(self) -> float:
        if self.pending is None:
            return 0.0
        return max(0.0, self.pending.complete_at - self.time_provider())

    def cook_duration(self, recipe: CookingRecipe) -> float:
        current_level = _skill_level(self.skills, "cooking")
        level_advantage = max(0, current_level - recipe.required_level)
        speed_bonus = min(0.50, 0.10 * level_advantage)
        return max(0.75, recipe.base_cook_seconds * (1.0 - speed_bonus))


def _recipes_from_items(item_definitions: dict[str, dict[str, object]]) -> dict[str, CookingRecipe]:
    recipes: dict[str, CookingRecipe] = {}
    for item_id, definition in item_definitions.items():
        cooked_item_id = definition.get("cook_result")
        if not cooked_item_id:
            continue
        recipes[item_id] = CookingRecipe(
            raw_item_id=item_id,
            cooked_item_id=str(cooked_item_id),
            required_level=int(definition["cooking_required_level"]),
            xp_reward=int(definition["cooking_xp"]),
            base_cook_seconds=float(definition["base_cook_seconds"]),
        )
    return recipes


def _skill_level(skills: Any, skill_id: str) -> int:
    if hasattr(skills, "level"):
        return int(skills.level(skill_id))
    return int(skills.get(skill_id).level)


def _skill_name(skills: Any, skill_id: str) -> str:
    if hasattr(skills, "display_name"):
        return str(skills.display_name(skill_id))
    return skill_id.replace("_", " ").title()


def _item_name(item_definitions: dict[str, dict[str, object]], item_id: str) -> str:
    return str(item_definitions.get(item_id, {}).get("name") or item_id.replace("_", " "))


def _start_feedback(
    item_definitions: dict[str, dict[str, object]],
    raw_item_id: str,
    duration: float,
) -> str:
    return f"Cooking {_item_name(item_definitions, raw_item_id)}... {duration:.1f}s"


def _pending_feedback(
    item_definitions: dict[str, dict[str, object]],
    raw_item_id: str,
    remaining_seconds: float,
) -> str:
    return f"Cooking {_item_name(item_definitions, raw_item_id)}... {remaining_seconds:.1f}s"


def _success_feedback(
    item_definitions: dict[str, dict[str, object]],
    skills: Any,
    recipe: CookingRecipe,
) -> str:
    raw_name = _item_name(item_definitions, recipe.raw_item_id)
    cooked_name = _item_name(item_definitions, recipe.cooked_item_id)
    return (
        f"Cooked {raw_name}: +1 {cooked_name}, "
        f"+{recipe.xp_reward} {_skill_name(skills, 'cooking')} XP"
    )
