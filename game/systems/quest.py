from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


STARTER_QUEST_ID = "starter_path"
STARTER_QUEST_FLAGS = (
    "cooked_food",
    "smelted_bar",
    "smithed_gear",
    "equipped_weapon",
    "ate_food",
    "defeated_enemy",
    "used_bank",
    "used_shop",
)


@dataclass
class QuestState:
    quest_id: str = STARTER_QUEST_ID
    started: bool = False
    completed: bool = False
    flags: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "QuestState":
        if not isinstance(data, dict):
            return cls()
        flags = data.get("flags", [])
        return cls(
            quest_id=str(data.get("quest_id") or STARTER_QUEST_ID),
            started=bool(data.get("started", False)),
            completed=bool(data.get("completed", False)),
            flags={str(flag) for flag in flags if str(flag) in STARTER_QUEST_FLAGS},
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "quest_id": self.quest_id,
            "started": self.started,
            "completed": self.completed,
            "flags": sorted(self.flags),
        }


@dataclass(frozen=True)
class QuestResult:
    feedback: str
    completed: bool = False


class QuestSystem:
    def __init__(self, state: QuestState | None = None) -> None:
        self.state = state or QuestState()

    def talk_to_starter(self) -> QuestResult:
        if self.state.completed:
            return QuestResult("Guide: The village is safer because of you.")
        if not self.state.started:
            self.state.started = True
            return QuestResult(
                "Guide: Cook food, smelt a bar, smith and equip a weapon, defeat an enemy, use the bank and shop, then return."
            )
        missing = [flag for flag in STARTER_QUEST_FLAGS if flag not in self.state.flags]
        if missing:
            return QuestResult(f"Guide: Keep going. Still needed: {', '.join(_flag_label(flag) for flag in missing)}.")
        self.state.completed = True
        return QuestResult("Quest complete: Starter path. Reward: 50 coins, +40 Smithing XP.", completed=True)

    def record(self, flag: str) -> bool:
        if flag not in STARTER_QUEST_FLAGS or self.state.completed:
            return False
        self.state.flags.add(flag)
        return True

    def to_dict(self) -> dict[str, object]:
        return self.state.to_dict()

    def load_dict(self, data: dict[str, Any] | None) -> None:
        self.state = QuestState.from_dict(data)


def _flag_label(flag: str) -> str:
    return flag.replace("_", " ")
