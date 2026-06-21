from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

from game.systems.inventory import inventory_can_transact


TimeProvider = Callable[[], float]


@dataclass(frozen=True)
class SmithingRecipe:
    recipe_id: str
    display_name: str
    action_type: str
    inputs: dict[str, int]
    output_item_id: str
    output_quantity: int
    required_level: int
    xp_reward: int
    base_seconds: float

    @classmethod
    def from_dict(cls, action_type: str, data: dict[str, Any]) -> "SmithingRecipe":
        inputs = {
            str(item_id): int(quantity)
            for item_id, quantity in data.get("inputs", {}).items()
            if int(quantity) > 0
        }
        raw_display_name = data.get("display_name")
        display_name = (
            str(raw_display_name)
            if isinstance(raw_display_name, str) and raw_display_name
            else str(data["recipe_id"]).replace("_", " ").title()
        )
        return cls(
            recipe_id=str(data["recipe_id"]),
            display_name=display_name,
            action_type=action_type,
            inputs=inputs,
            output_item_id=str(data["output_item_id"]),
            output_quantity=int(data.get("output_quantity", 1)),
            required_level=int(data["required_level"]),
            xp_reward=int(data["xp_reward"]),
            base_seconds=float(data["base_seconds"]),
        )


@dataclass(frozen=True)
class PendingSmithing:
    recipe_id: str
    action_type: str
    complete_at: float
    duration: float


@dataclass(frozen=True)
class SmithingResult:
    success: bool
    feedback: str
    recipe_id: str | None = None
    item_id: str | None = None
    quantity: int = 0
    xp: int = 0
    pending: bool = False
    needs_choice: bool = False
    duration: float = 0.0


class SmithingSystem:
    def __init__(
        self,
        recipes_data: dict[str, Any],
        inventory: Any,
        skills: Any,
        *,
        item_definitions: dict[str, dict[str, object]] | None = None,
        time_provider: TimeProvider = time.time,
    ) -> None:
        self.inventory = inventory
        self.skills = skills
        self.item_definitions = item_definitions or {}
        self.time_provider = time_provider
        self.recipes = _recipes_from_data(recipes_data)
        self.pending: PendingSmithing | None = None

    def start_smelting(self, selected_item_id: str | None) -> SmithingResult:
        recipes = self.matching_recipes("smelting", selected_item_id)
        if not recipes:
            return SmithingResult(False, "Select ore to smelt")
        if len(recipes) > 1:
            return SmithingResult(False, "Choose a recipe to smelt", needs_choice=True)
        return self.start_recipe(recipes[0])

    def start_smithing(self, selected_item_id: str | None) -> SmithingResult:
        recipes = self.matching_recipes("smithing", selected_item_id)
        if not recipes:
            return SmithingResult(False, "Select bars to smith")
        if len(recipes) > 1:
            return SmithingResult(False, "Choose a recipe to smith", needs_choice=True)
        return self.start_recipe(recipes[0])

    def start_recipe_by_id(self, action_type: str, recipe_id: str) -> SmithingResult:
        recipe = self.recipe_by_id(action_type, recipe_id)
        if recipe is None:
            return SmithingResult(False, "Recipe unavailable", recipe_id=recipe_id)
        return self.start_recipe(recipe)

    def start_recipe(self, recipe: SmithingRecipe) -> SmithingResult:
        if self.pending is not None:
            if self.pending.recipe_id == recipe.recipe_id and self.pending.action_type == recipe.action_type:
                return SmithingResult(
                    True,
                    _pending_feedback(recipe, self.remaining_seconds()),
                    recipe_id=recipe.recipe_id,
                    item_id=recipe.output_item_id,
                    pending=True,
                    duration=self.pending.duration,
                )
            self.cancel_pending()

        current_level = _skill_level(self.skills, "smithing")
        if current_level < recipe.required_level:
            return SmithingResult(False, f"You need Smithing level {recipe.required_level}", recipe_id=recipe.recipe_id)

        missing = _missing_inputs(self.inventory, recipe.inputs)
        if missing:
            return SmithingResult(False, f"You need {missing}", recipe_id=recipe.recipe_id)
        if not inventory_can_transact(
            self.inventory.to_dict(),
            self.item_definitions,
            remove=recipe.inputs,
            add={recipe.output_item_id: recipe.output_quantity},
        ):
            return SmithingResult(False, "Inventory is full", recipe_id=recipe.recipe_id)

        duration = self.action_duration(recipe)
        self.pending = PendingSmithing(
            recipe_id=recipe.recipe_id,
            action_type=recipe.action_type,
            complete_at=self.time_provider() + duration,
            duration=duration,
        )
        return SmithingResult(
            True,
            _start_feedback(recipe, duration),
            recipe_id=recipe.recipe_id,
            item_id=recipe.output_item_id,
            pending=True,
            duration=duration,
        )

    def update(self) -> SmithingResult | None:
        if self.pending is None or self.time_provider() < self.pending.complete_at:
            return None

        pending = self.pending
        self.pending = None
        recipe = self.recipes.get(pending.action_type, {}).get(pending.recipe_id)
        if recipe is None:
            return SmithingResult(False, "No recipe selected")

        missing = _missing_inputs(self.inventory, recipe.inputs)
        if missing:
            return SmithingResult(False, f"You need {missing}", recipe_id=recipe.recipe_id)
        if not inventory_can_transact(
            self.inventory.to_dict(),
            self.item_definitions,
            remove=recipe.inputs,
            add={recipe.output_item_id: recipe.output_quantity},
        ):
            return SmithingResult(False, "Inventory is full", recipe_id=recipe.recipe_id)

        for item_id, quantity in recipe.inputs.items():
            self.inventory.remove(item_id, quantity)
        self.inventory.add(recipe.output_item_id, recipe.output_quantity)
        self.skills.add_xp("smithing", recipe.xp_reward)
        return SmithingResult(
            True,
            _success_feedback(recipe),
            recipe_id=recipe.recipe_id,
            item_id=recipe.output_item_id,
            quantity=recipe.output_quantity,
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

    def action_duration(self, recipe: SmithingRecipe) -> float:
        current_level = _skill_level(self.skills, "smithing")
        level_advantage = max(0, current_level - recipe.required_level)
        speed_bonus = min(0.50, 0.05 * level_advantage)
        return max(0.75, recipe.base_seconds * (1.0 - speed_bonus))

    def matching_recipes(self, action_type: str, selected_item_id: str | None) -> list[SmithingRecipe]:
        if selected_item_id is None:
            return []
        return [
            recipe
            for recipe in self.recipes.get(action_type, {}).values()
            if selected_item_id in recipe.inputs
        ]

    def recipe_by_id(self, action_type: str, recipe_id: str) -> SmithingRecipe | None:
        return self.recipes.get(action_type, {}).get(recipe_id)

    def recipe_for_item(self, action_type: str, selected_item_id: str | None) -> SmithingRecipe | None:
        recipes = self.matching_recipes(action_type, selected_item_id)
        if not recipes:
            return None
        return recipes[0]


def _recipes_from_data(data: dict[str, Any]) -> dict[str, dict[str, SmithingRecipe]]:
    recipes: dict[str, dict[str, SmithingRecipe]] = {"smelting": {}, "smithing": {}}
    for action_type in recipes:
        for raw_recipe in data.get(action_type, []) or []:
            if not isinstance(raw_recipe, dict):
                continue
            recipe = SmithingRecipe.from_dict(action_type, raw_recipe)
            recipes[action_type][recipe.recipe_id] = recipe
    return recipes


def _skill_level(skills: Any, skill_id: str) -> int:
    if hasattr(skills, "level"):
        return int(skills.level(skill_id))
    return int(skills.get(skill_id).level)


def _missing_inputs(inventory: Any, inputs: dict[str, int]) -> str:
    missing: list[str] = []
    for item_id, quantity in inputs.items():
        available = inventory.count(item_id)
        if available < quantity:
            missing.append(f"{quantity - available} {item_id.replace('_', ' ')}")
    return ", ".join(missing)


def _start_feedback(recipe: SmithingRecipe, duration: float) -> str:
    verb = "Smelting" if recipe.action_type == "smelting" else "Smithing"
    return f"{verb} {recipe.display_name}... {duration:.1f}s"


def _pending_feedback(recipe: SmithingRecipe, remaining_seconds: float) -> str:
    verb = "Smelting" if recipe.action_type == "smelting" else "Smithing"
    return f"{verb} {recipe.display_name}... {remaining_seconds:.1f}s"


def _success_feedback(recipe: SmithingRecipe) -> str:
    verb = "Smelted" if recipe.action_type == "smelting" else "Smithed"
    return (
        f"{verb} {recipe.display_name}: +{recipe.output_quantity} "
        f"{recipe.output_item_id.replace('_', ' ')}, +{recipe.xp_reward} Smithing XP"
    )
