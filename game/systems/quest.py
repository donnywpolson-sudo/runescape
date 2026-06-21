from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from game.systems.inventory import COINS_ITEM_ID


STARTER_QUEST_ID = "starter_path"

@dataclass
class QuestState:
    quest_id: str = STARTER_QUEST_ID
    started: bool = False
    completed: bool = False
    flags: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any] | None,
        valid_flags: Iterable[str] | None = None,
        default_quest_id: str = STARTER_QUEST_ID,
    ) -> "QuestState":
        if not isinstance(data, dict):
            return cls(quest_id=default_quest_id)
        flags = data.get("flags", [])
        valid_flag_set = set(valid_flags) if valid_flags is not None else None
        return cls(
            quest_id=str(data.get("quest_id") or default_quest_id),
            started=bool(data.get("started", False)),
            completed=bool(data.get("completed", False)),
            flags={str(flag) for flag in flags if valid_flag_set is None or str(flag) in valid_flag_set},
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "quest_id": self.quest_id,
            "started": self.started,
            "completed": self.completed,
            "flags": sorted(self.flags),
        }


@dataclass(frozen=True)
class QuestObjective:
    text: str
    completed: bool = False


@dataclass(frozen=True)
class QuestItemReward:
    item_id: str
    quantity: int


@dataclass(frozen=True)
class QuestSkillReward:
    skill_id: str
    xp: int


@dataclass(frozen=True)
class QuestResult:
    feedback: str
    completed: bool = False
    item_rewards: tuple[QuestItemReward, ...] = ()
    skill_rewards: tuple[QuestSkillReward, ...] = ()


@dataclass(frozen=True)
class QuestObjectiveDefinition:
    flag: str
    label: str


@dataclass(frozen=True)
class QuestDefinition:
    quest_id: str
    display_name: str
    start_text: str
    in_progress_text: str
    completed_text: str
    completion_text: str
    not_started_objective: str
    return_objective: str
    completed_objective: str
    progress_format: str
    objectives: tuple[QuestObjectiveDefinition, ...]
    item_rewards: tuple[QuestItemReward, ...] = ()
    skill_rewards: tuple[QuestSkillReward, ...] = ()

    @property
    def flags(self) -> tuple[str, ...]:
        return tuple(objective.flag for objective in self.objectives)


STARTER_QUEST_DEFINITION = QuestDefinition(
    quest_id=STARTER_QUEST_ID,
    display_name="Starter path",
    start_text=(
        "Guide: Cook food, smelt a bar, smith and equip a weapon, "
        "defeat an enemy, use the bank and shop, then return."
    ),
    in_progress_text="Guide: Keep going. Still needed: {missing_objectives}.",
    completed_text="Guide: The village is safer because of you.",
    completion_text="Quest complete: Starter path. Reward: 50 coins, +40 Smithing XP.",
    not_started_objective="Talk to the Village Guide.",
    return_objective="Return to the Village Guide.",
    completed_objective="Starter path complete.",
    progress_format="Starter path {completed}/{total}: {objective}.",
    objectives=(
        QuestObjectiveDefinition("cooked_food", "Cook food"),
        QuestObjectiveDefinition("smelted_bar", "Smelt a bar"),
        QuestObjectiveDefinition("smithed_gear", "Smith gear"),
        QuestObjectiveDefinition("equipped_weapon", "Equip a weapon"),
        QuestObjectiveDefinition("ate_food", "Eat food"),
        QuestObjectiveDefinition("defeated_enemy", "Defeat an enemy"),
        QuestObjectiveDefinition("used_bank", "Use the bank"),
        QuestObjectiveDefinition("used_shop", "Use the shop"),
    ),
    item_rewards=(QuestItemReward(COINS_ITEM_ID, 50),),
    skill_rewards=(QuestSkillReward("smithing", 40),),
)
STARTER_QUEST_FLAGS = STARTER_QUEST_DEFINITION.flags


class QuestSystem:
    def __init__(
        self,
        definitions_data: dict[str, Any] | QuestState | None = None,
        state: QuestState | None = None,
    ) -> None:
        if isinstance(definitions_data, QuestState) and state is None:
            state = definitions_data
            definitions_data = None
        self.definitions = quest_definitions_from_data(definitions_data)
        self.definition = self.definitions.get(STARTER_QUEST_ID, STARTER_QUEST_DEFINITION)
        self.active_quest_id = state.quest_id if state is not None else self.definition.quest_id
        self.states: dict[str, QuestState] = {}
        if state is not None:
            self.states[state.quest_id] = state

    def talk_to_starter(self) -> QuestResult:
        return self.talk_to(STARTER_QUEST_ID)

    def pending_completion_item_rewards(self, quest_id: str) -> tuple[QuestItemReward, ...]:
        definition = self.definitions.get(quest_id)
        if definition is None:
            return ()
        state = self._state_for(definition.quest_id)
        if state.completed or not state.started:
            return ()
        if any(objective.flag not in state.flags for objective in definition.objectives):
            return ()
        return definition.item_rewards

    def talk_to(self, quest_id: str) -> QuestResult:
        definition = self.definitions.get(quest_id)
        if definition is None:
            return QuestResult("")
        self.active_quest_id = definition.quest_id
        state = self._state_for(definition.quest_id)
        if state.completed:
            return QuestResult(definition.completed_text)
        if not state.started:
            state.started = True
            return QuestResult(definition.start_text)
        missing = [objective for objective in definition.objectives if objective.flag not in state.flags]
        if missing:
            missing_text = ", ".join(objective.label.lower() for objective in missing)
            return QuestResult(definition.in_progress_text.format(missing_objectives=missing_text))
        state.completed = True
        return QuestResult(
            definition.completion_text,
            completed=True,
            item_rewards=definition.item_rewards,
            skill_rewards=definition.skill_rewards,
        )

    def record(self, flag: str) -> bool:
        recorded = False
        for quest_id, definition in self.definitions.items():
            if flag not in definition.flags:
                continue
            state = self.states.get(quest_id)
            if state is None:
                if quest_id != self.active_quest_id:
                    continue
                state = self._state_for(quest_id)
            if state.completed:
                continue
            state.flags.add(flag)
            recorded = True
        return recorded

    def current_objective(self) -> QuestObjective:
        definition = self.definitions.get(self.active_quest_id, self.definition)
        state = self._state_for(definition.quest_id)
        if state.completed:
            return QuestObjective(definition.completed_objective, completed=True)
        if not state.started:
            return QuestObjective(definition.not_started_objective)
        missing = [objective for objective in definition.objectives if objective.flag not in state.flags]
        if not missing:
            return QuestObjective(definition.return_objective)
        progress = len(definition.objectives) - len(missing)
        return QuestObjective(
            definition.progress_format.format(
                completed=progress,
                total=len(definition.objectives),
                objective=missing[0].label,
            )
        )

    def to_dict(self) -> dict[str, object]:
        quests = {
            quest_id: state.to_dict()
            for quest_id, state in sorted(self.states.items())
            if state.started or state.completed or state.flags
        }
        if not quests:
            return {}
        return {
            "active_quest_id": self.active_quest_id,
            "quests": quests,
        }

    def load_dict(self, data: dict[str, Any] | None) -> None:
        self.states.clear()
        self.active_quest_id = self.definition.quest_id
        if not isinstance(data, dict) or not data:
            return
        raw_states = data.get("quests")
        if isinstance(raw_states, dict):
            for quest_id, raw_state in raw_states.items():
                if quest_id not in self.definitions:
                    continue
                definition = self.definitions[quest_id]
                state = QuestState.from_dict(raw_state, definition.flags, definition.quest_id)
                state.quest_id = definition.quest_id
                self.states[definition.quest_id] = state
            active_quest_id = str(data.get("active_quest_id") or self.definition.quest_id)
            if active_quest_id in self.definitions:
                self.active_quest_id = active_quest_id
            return

        state = QuestState.from_dict(data, self.definition.flags, self.definition.quest_id)
        if state.quest_id not in self.definitions:
            state.quest_id = self.definition.quest_id
        self.states[state.quest_id] = state
        self.active_quest_id = state.quest_id

    @property
    def state(self) -> QuestState:
        return self._state_for(self.active_quest_id)

    @state.setter
    def state(self, state: QuestState) -> None:
        self.active_quest_id = state.quest_id
        self.states[state.quest_id] = state

    def _state_for(self, quest_id: str) -> QuestState:
        definition = self.definitions.get(quest_id, self.definition)
        state = self.states.get(definition.quest_id)
        if state is None:
            state = QuestState(quest_id=definition.quest_id)
            self.states[definition.quest_id] = state
        return state


def quest_definitions_from_data(data: dict[str, Any] | None) -> dict[str, QuestDefinition]:
    if not isinstance(data, dict):
        return {STARTER_QUEST_ID: STARTER_QUEST_DEFINITION}
    definitions: dict[str, QuestDefinition] = {}
    for raw_quest in data.get("quests", []) or []:
        if not isinstance(raw_quest, dict):
            continue
        definition = _quest_definition_from_dict(raw_quest)
        definitions[definition.quest_id] = definition
    definitions.setdefault(STARTER_QUEST_ID, STARTER_QUEST_DEFINITION)
    return definitions


def _quest_definition_from_dict(data: dict[str, Any]) -> QuestDefinition:
    return QuestDefinition(
        quest_id=str(data["quest_id"]),
        display_name=str(data["display_name"]),
        start_text=str(data["start_text"]),
        in_progress_text=str(data["in_progress_text"]),
        completed_text=str(data["completed_text"]),
        completion_text=str(data["completion_text"]),
        not_started_objective=str(data["not_started_objective"]),
        return_objective=str(data["return_objective"]),
        completed_objective=str(data["completed_objective"]),
        progress_format=str(data["progress_format"]),
        objectives=tuple(
            QuestObjectiveDefinition(str(objective["flag"]), str(objective["label"]))
            for objective in data.get("objectives", [])
            if isinstance(objective, dict)
        ),
        item_rewards=tuple(
            QuestItemReward(str(reward["item_id"]), int(reward["quantity"]))
            for reward in data.get("item_rewards", [])
            if isinstance(reward, dict)
        ),
        skill_rewards=tuple(
            QuestSkillReward(str(reward["skill_id"]), int(reward["xp"]))
            for reward in data.get("skill_rewards", [])
            if isinstance(reward, dict)
        ),
    )
