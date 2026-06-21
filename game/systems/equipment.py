from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EQUIPMENT_SLOTS = ("weapon", "shield")


@dataclass(frozen=True)
class EquipmentResult:
    success: bool
    feedback: str


@dataclass
class Equipment:
    item_definitions: dict[str, dict[str, object]]
    inventory: Any
    skills: Any
    slots: dict[str, str] = field(default_factory=dict)

    def is_equippable(self, item_id: str) -> bool:
        return bool(self._definition(item_id).get("equip_slot"))

    def equip(self, item_id: str) -> EquipmentResult:
        definition = self._definition(item_id)
        slot = str(definition.get("equip_slot") or "")
        if slot not in EQUIPMENT_SLOTS:
            return EquipmentResult(False, f"{self._item_name(item_id)} cannot be equipped")
        if self.inventory.count(item_id) <= 0:
            return EquipmentResult(False, f"No {self._item_name(item_id)} to equip")

        for skill_id, required_level in _required_skills(definition).items():
            current_level = _skill_level(self.skills, skill_id)
            if current_level < required_level:
                return EquipmentResult(
                    False,
                    f"You need {_skill_name(self.skills, skill_id)} level {required_level} to wield {self._item_name(item_id)}",
                )

        self.inventory.remove(item_id, 1)
        replaced_item_id = self.slots.get(slot)
        if replaced_item_id:
            self.inventory.add(replaced_item_id, 1)
        self.slots[slot] = item_id
        return EquipmentResult(True, f"Equipped {self._item_name(item_id)}")

    def unequip(self, slot: str) -> EquipmentResult:
        if slot not in EQUIPMENT_SLOTS:
            return EquipmentResult(False, "Unknown equipment slot")
        item_id = self.slots.get(slot)
        if item_id is None:
            return EquipmentResult(False, f"No {slot} equipped")
        if hasattr(self.inventory, "can_add") and not self.inventory.can_add(item_id, 1, item_definitions=self.item_definitions):
            return EquipmentResult(False, "Inventory is full")
        self.slots.pop(slot, None)
        self.inventory.add(item_id, 1)
        return EquipmentResult(True, f"Unequipped {self._item_name(item_id)}")

    def to_dict(self) -> dict[str, str]:
        return {
            slot: item_id
            for slot, item_id in sorted(self.slots.items())
            if slot in EQUIPMENT_SLOTS and self.is_equippable(item_id)
        }

    def load_dict(self, data: dict[str, object] | None) -> None:
        self.slots.clear()
        if not isinstance(data, dict):
            return
        for slot, item_id in data.items():
            slot = str(slot)
            item_id = str(item_id)
            if slot in EQUIPMENT_SLOTS and self.is_equippable(item_id):
                self.slots[slot] = item_id

    def _definition(self, item_id: str) -> dict[str, object]:
        return self.item_definitions.get(item_id, {})

    def _item_name(self, item_id: str) -> str:
        return str(self._definition(item_id).get("name") or item_id.replace("_", " "))


def _required_skills(definition: dict[str, object]) -> dict[str, int]:
    raw_requirements = definition.get("required_skills")
    if not isinstance(raw_requirements, dict):
        return {}
    requirements: dict[str, int] = {}
    for skill_id, raw_level in raw_requirements.items():
        requirements[str(skill_id)] = int(raw_level)
    return requirements


def _skill_level(skills: Any, skill_id: str) -> int:
    if hasattr(skills, "level"):
        return int(skills.level(skill_id))
    return int(skills.get(skill_id).level)


def _skill_name(skills: Any, skill_id: str) -> str:
    if hasattr(skills, "display_name"):
        return str(skills.display_name(skill_id))
    definition = getattr(skills, "definitions", {}).get(skill_id, {})
    return str(definition.get("display_name") or definition.get("name") or skill_id.replace("_", " "))
