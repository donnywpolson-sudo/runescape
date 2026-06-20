from __future__ import annotations

from dataclasses import dataclass
from typing import Any


XP_PER_LEVEL = 100


@dataclass
class SkillState:
    level: int = 1
    xp: int = 0


class Skills:
    def __init__(self, definitions: dict[str, Any] | list[dict[str, Any]] | None = None) -> None:
        self.definitions = _normalize_definitions(definitions)
        self.states: dict[str, SkillState] = {}
        for skill_id, definition in self.definitions.items():
            xp = int(definition.get("xp", 0))
            self.states[skill_id] = SkillState(
                level=int(definition.get("starting_level", level_for_xp(xp))),
                xp=xp,
            )

    def add_skill(self, skill_id: str, xp: int = 0) -> SkillState:
        state = SkillState(level=self.level_for_xp(skill_id, xp), xp=xp)
        self.states[skill_id] = state
        return state

    def add_xp(self, skill_id: str, amount: int) -> int:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        state = self.states.get(skill_id) or self.add_skill(skill_id)
        state.xp += amount
        state.level = self.level_for_xp(skill_id, state.xp)
        return state.level

    def level(self, skill_id: str) -> int:
        return self.states.get(skill_id, SkillState()).level

    def xp(self, skill_id: str) -> int:
        return self.states.get(skill_id, SkillState()).xp

    def display_name(self, skill_id: str) -> str:
        definition = self.definitions.get(skill_id, {})
        return str(
            definition.get("display_name")
            or definition.get("name")
            or skill_id.replace("_", " ").title()
        )

    def level_for_xp(self, skill_id: str, xp: int) -> int:
        if xp < 0:
            raise ValueError("xp must be non-negative")
        thresholds = self.definitions.get(skill_id, {}).get("xp_thresholds")
        if thresholds:
            level = 1
            for threshold_level, threshold_xp in sorted(
                (int(level), int(xp_value)) for level, xp_value in thresholds.items()
            ):
                if xp >= threshold_xp:
                    level = threshold_level
            return level
        return level_for_xp(xp)

    def action_xp(self, skill_id: str, action_id: str) -> int:
        return int(self.definitions[skill_id]["actions"][action_id]["xp"])

    def get(self, skill_id: str) -> SkillState:
        return self.states.get(skill_id) or self.add_skill(skill_id)

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {
            skill_id: {"level": state.level, "xp": state.xp}
            for skill_id, state in sorted(self.states.items())
        }

    def load_dict(self, data: dict[str, dict[str, int]]) -> None:
        for skill_id, values in data.items():
            xp = int(values.get("xp", 0))
            state = self.states.get(skill_id) or self.add_skill(skill_id)
            state.xp = xp
            state.level = self.level_for_xp(skill_id, xp)


def level_for_xp(xp: int) -> int:
    if xp < 0:
        raise ValueError("xp must be non-negative")
    return 1 + xp // XP_PER_LEVEL


def _normalize_definitions(
    definitions: dict[str, Any] | list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if definitions is None:
        return {}
    if isinstance(definitions, dict):
        return definitions
    return {str(definition["id"]): definition for definition in definitions}
