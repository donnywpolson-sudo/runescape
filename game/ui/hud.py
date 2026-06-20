from __future__ import annotations

from collections.abc import Callable
from typing import Any

from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode


PANEL = (0.26, 0.18, 0.10, 0.90)
PANEL_DARK = (0.12, 0.08, 0.04, 0.92)
PANEL_LIGHT = (0.47, 0.34, 0.18, 0.96)
SLOT = (0.17, 0.11, 0.06, 0.96)
SLOT_HILITE = (0.62, 0.48, 0.25, 1.0)
BUTTON = (0.48, 0.34, 0.16, 1.0)
BUTTON_HOVER = (0.60, 0.43, 0.21, 1.0)
TEXT = (0.96, 0.88, 0.68, 1.0)
MUTED_TEXT = (0.82, 0.76, 0.62, 1.0)
GOLD = (1.0, 0.78, 0.28, 1.0)


class Hud:
    def __init__(
        self,
        items_data: dict[str, dict[str, object]] | None = None,
        _skills_data: dict[str, dict[str, object]] | None = None,
        *,
        on_bank_close: Callable[[], None] | None = None,
        on_deposit_item: Callable[[str], None] | None = None,
        on_withdraw_item: Callable[[str], None] | None = None,
        on_deposit_all: Callable[[], None] | None = None,
    ) -> None:
        self.items_data = items_data or {}
        self.on_bank_close = on_bank_close or (lambda: None)
        self.on_deposit_item = on_deposit_item or (lambda _item_id: None)
        self.on_withdraw_item = on_withdraw_item or (lambda _item_id: None)
        self.on_deposit_all = on_deposit_all or (lambda: None)
        self.bank_is_open = False

        self.stats_panel = _frame((-0.02, 0.62, -0.22, 0.03), (-1.35, 0, 0.91), PANEL)
        self.stats = _text(self.stats_panel, "", (0.03, -0.04), 0.033, TextNode.ALeft, TEXT, True)

        self.feedback_panel = _frame((-0.48, 0.48, -0.05, 0.025), (0.0, 0, 0.91), PANEL_DARK)
        self.feedback = _text(self.feedback_panel, "", (0.0, -0.025), 0.034, TextNode.ACenter, GOLD, True)

        self.side_panel = _frame((-0.26, 0.26, -0.84, 0.18), (1.48, 0, 0.74), PANEL)
        _text(self.side_panel, "RuneScape Valley", (0.0, 0.115), 0.034, TextNode.ACenter, GOLD)

        self.minimap = _frame((-0.18, 0.18, -0.18, 0.18), (0.0, 0, -0.08), PANEL_LIGHT, self.side_panel)
        _text(self.minimap, "N", (0.0, 0.135), 0.025, TextNode.ACenter, PANEL_DARK)
        _frame((-0.016, 0.016, -0.016, 0.016), (0.0, 0, 0.0), (0.88, 0.26, 0.16, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (-0.08, 0, -0.04), (0.14, 0.32, 0.76, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (0.10, 0, 0.06), (0.10, 0.44, 0.14, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (0.12, 0, -0.08), (0.68, 0.44, 0.20, 1), self.minimap)

        _text(self.side_panel, "Inventory", (0.0, -0.32), 0.030, TextNode.ACenter, GOLD)
        self.category_labels: dict[str, OnscreenText] = {}
        self._make_category_slot("wood", "Wood", -0.13, -0.46)
        self._make_category_slot("ore", "Ore", 0.0, -0.46)
        self._make_category_slot("fish", "Fish", 0.13, -0.46)

        _text(self.side_panel, "Skills", (0.0, -0.61), 0.030, TextNode.ACenter, GOLD)
        self.skills = _text(self.side_panel, "", (-0.21, -0.675), 0.027, TextNode.ALeft, MUTED_TEXT, True)

        self.help_panel = _frame((-1.18, 1.18, -0.045, 0.025), (0.0, 0, -0.93), PANEL_DARK)
        self.help = _text(
            self.help_panel,
            "WASD camera | Q/E rotate | Wheel zoom | Left click move | Right click interact | F5 save | F9 load | Esc quit",
            (-1.14, -0.015),
            0.027,
            TextNode.ALeft,
            MUTED_TEXT,
        )

        self.bank_panel = _frame((-0.72, 0.72, -0.56, 0.58), (0.0, 0, 0.02), PANEL)
        _text(self.bank_panel, "Bank", (0.0, 0.51), 0.045, TextNode.ACenter, GOLD)
        _button(self.bank_panel, "Close", (0.54, 0, 0.50), 0.040, self.on_bank_close)
        _button(self.bank_panel, "Deposit all", (-0.48, 0, 0.50), 0.035, self.on_deposit_all)
        _text(self.bank_panel, "Item", (-0.62, 0.43), 0.026, TextNode.ALeft, GOLD)
        _text(self.bank_panel, "Inv", (0.02, 0.43), 0.026, TextNode.ACenter, GOLD)
        _text(self.bank_panel, "Bank", (0.16, 0.43), 0.026, TextNode.ACenter, GOLD)
        self.bank_rows: dict[str, tuple[OnscreenText, OnscreenText]] = {}
        self._build_bank_rows()
        self.bank_panel.hide()

    def update(
        self,
        *,
        account: str,
        time_text: str,
        coins: int,
        selected_text: str,
        inventory: dict[str, int],
        bank: dict[str, int],
        skills: Any,
    ) -> None:
        self.stats.setText("\n".join([f"Account: {account}", time_text, f"Coins: {coins}", selected_text]))
        for category, label in self.category_labels.items():
            label.setText(f"{category.title()}\n{_category_total(self.items_data, inventory, category)}")

        self.skills.setText(
            "\n".join(
                [
                    _compact_skill("Wood", skills.get("woodcutting")),
                    _compact_skill("Mine", skills.get("mining")),
                    _compact_skill("Fish", skills.get("fishing")),
                ]
            )
        )

        for item_id, (inventory_label, bank_label) in self.bank_rows.items():
            inventory_label.setText(str(inventory.get(item_id, 0)))
            bank_label.setText(str(bank.get(item_id, 0)))

    def set_feedback(self, message: str) -> None:
        self.feedback.setText(message)

    def open_bank(self) -> None:
        self.bank_is_open = True
        self.bank_panel.show()

    def close_bank(self) -> None:
        self.bank_is_open = False
        self.bank_panel.hide()

    def _make_category_slot(self, category: str, label: str, x: float, z: float) -> None:
        slot = _frame((-0.055, 0.055, -0.055, 0.055), (x, 0, z), SLOT, self.side_panel)
        _frame((-0.041, 0.041, 0.029, 0.041), (0.0, 0, 0.0), SLOT_HILITE, slot)
        self.category_labels[category] = _text(slot, f"{label}\n0", (0.0, -0.022), 0.023, TextNode.ACenter, TEXT, True)

    def _build_bank_rows(self) -> None:
        for index, item_id in enumerate(sorted(self.items_data, key=lambda item_id: (_category_sort_key(self.items_data, item_id), item_id))):
            y = 0.36 - index * 0.058
            _text(self.bank_panel, _item_name(self.items_data, item_id), (-0.62, y), 0.022, TextNode.ALeft, TEXT)
            inventory_label = _text(self.bank_panel, "0", (0.02, y), 0.022, TextNode.ACenter, TEXT, True)
            bank_label = _text(self.bank_panel, "0", (0.16, y), 0.022, TextNode.ACenter, TEXT, True)
            _button(self.bank_panel, "Dep", (0.34, 0, y + 0.004), 0.025, lambda item_id=item_id: self.on_deposit_item(item_id))
            _button(self.bank_panel, "Wit", (0.53, 0, y + 0.004), 0.025, lambda item_id=item_id: self.on_withdraw_item(item_id))
            self.bank_rows[item_id] = (inventory_label, bank_label)


def _frame(
    frame_size: tuple[float, float, float, float],
    pos: tuple[float, float, float],
    color: tuple[float, float, float, float],
    parent: Any | None = None,
) -> DirectFrame:
    kwargs: dict[str, Any] = {"frameSize": frame_size, "frameColor": color, "pos": pos}
    if parent is not None:
        kwargs["parent"] = parent
    return DirectFrame(**kwargs)


def _button(parent: Any, text: str, pos: tuple[float, float, float], scale: float, command: Callable[[], None]) -> DirectButton:
    return DirectButton(
        parent=parent,
        text=text,
        pos=pos,
        scale=scale,
        frameColor=(BUTTON, BUTTON_HOVER, BUTTON_HOVER, BUTTON),
        text_fg=TEXT,
        command=command,
    )


def _text(
    parent: Any,
    text: str,
    pos: tuple[float, float],
    scale: float,
    align: int,
    color: tuple[float, float, float, float],
    may_change: bool = False,
) -> OnscreenText:
    return OnscreenText(parent=parent, text=text, pos=pos, scale=scale, align=align, fg=color, mayChange=may_change)


def _category_total(
    items_data: dict[str, dict[str, object]],
    inventory: dict[str, int],
    category: str,
) -> int:
    total = 0
    for item_id, quantity in inventory.items():
        if items_data.get(item_id, {}).get("category") == category:
            total += int(quantity)
    return total


def _compact_skill(label: str, state: Any) -> str:
    return f"{label}: lvl {state.level} ({state.xp} XP)"


def _item_name(items_data: dict[str, dict[str, object]], item_id: str) -> str:
    return str(items_data.get(item_id, {}).get("name") or item_id.replace("_", " "))


def _category_sort_key(items_data: dict[str, dict[str, object]], item_id: str) -> tuple[int, str]:
    category = str(items_data.get(item_id, {}).get("category") or "")
    return {"wood": 0, "ore": 1, "fish": 2}.get(category, 9), category
