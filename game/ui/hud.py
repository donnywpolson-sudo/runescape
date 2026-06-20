from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from direct.gui.DirectGui import DGG, DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from game.style import UiPalette as UI
from game.systems.inventory import COINS_ITEM_ID

PANEL = UI.PANEL
PANEL_DARK = UI.PANEL_DARK
PANEL_LIGHT = UI.PARCHMENT
SLOT = UI.SLOT
SLOT_HILITE = UI.SLOT_HILITE
BUTTON = UI.BUTTON
BUTTON_HOVER = UI.BUTTON_HOVER
TEXT = UI.TEXT
MUTED_TEXT = UI.MUTED_TEXT
GOLD = UI.GOLD

INVENTORY_TAB = "inventory"
CLOTHES_TAB = "clothes"
SKILLS_TAB = "skills"
TAB_ORDER = (INVENTORY_TAB, CLOTHES_TAB, SKILLS_TAB)
INVENTORY_COLUMNS = 4
INVENTORY_ROWS = 7
INVENTORY_SLOT_COUNT = INVENTORY_COLUMNS * INVENTORY_ROWS
INVENTORY_QUANTITY_TEXT_SCALE = 0.027
SIDE_TAB_TEXT_SCALE = 0.039
SKILL_ROW_SPACING = 0.095
SKILL_NAME_TEXT_SCALE = 0.031
SKILL_DETAIL_TEXT_SCALE = 0.026
ITEM_ICON_LABEL_TEXT_SCALE = 0.023
STATS_TEXT_SCALE = 0.036
FEEDBACK_TEXT_SCALE = 0.039
CHAT_VISIBLE_LINES = 8
CHAT_HISTORY_LIMIT = 100
CHAT_TEXT_SCALE = 0.027
ROW_TEXT_SCALE = 0.022
ROW_BUTTON_TEXT_SCALE = 0.023
SMALL_BUTTON_TEXT_SCALE = 0.023
IconSpec = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float],
    tuple[float, float, float, float],
]
DEFAULT_SKILL_IDS = (
    "woodcutting",
    "mining",
    "fishing",
    "cooking",
    "attack",
    "strength",
    "defence",
    "hitpoints",
    "smithing",
)
EQUIPMENT_SLOT_LAYOUT = (
    ("head", "Head", 0.00, -0.07),
    ("cape", "Cape", -0.13, -0.20),
    ("amulet", "Amulet", 0.00, -0.20),
    ("ammo", "Ammo", 0.13, -0.20),
    ("weapon", "Weapon", -0.13, -0.35),
    ("body", "Body", 0.00, -0.35),
    ("shield", "Shield", 0.13, -0.35),
    ("legs", "Legs", 0.00, -0.50),
    ("hands", "Hands", -0.13, -0.65),
    ("feet", "Feet", 0.00, -0.65),
    ("ring", "Ring", 0.13, -0.65),
)


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
        on_shop_close: Callable[[], None] | None = None,
        on_buy_item: Callable[[str], None] | None = None,
        on_sell_item: Callable[[str], None] | None = None,
        on_sell_all: Callable[[], None] | None = None,
        on_select_item: Callable[[str], None] | None = None,
        on_unequip_slot: Callable[[str], None] | None = None,
        on_save: Callable[[], None] | None = None,
        on_load: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ) -> None:
        self.items_data = items_data or {}
        self.skills_data = _skills_data or {}
        self.skill_ids = _skill_ids(self.skills_data)
        self.on_bank_close = on_bank_close or (lambda: None)
        self.on_deposit_item = on_deposit_item or (lambda _item_id: None)
        self.on_withdraw_item = on_withdraw_item or (lambda _item_id: None)
        self.on_deposit_all = on_deposit_all or (lambda: None)
        self.on_shop_close = on_shop_close or (lambda: None)
        self.on_buy_item = on_buy_item or (lambda _item_id: None)
        self.on_sell_item = on_sell_item or (lambda _item_id: None)
        self.on_sell_all = on_sell_all or (lambda: None)
        self.on_select_item = on_select_item or (lambda _item_id: None)
        self.on_unequip_slot = on_unequip_slot or (lambda _slot: None)
        self.on_save = on_save or (lambda: None)
        self.on_load = on_load or (lambda: None)
        self.on_quit = on_quit or (lambda: None)
        self.bank_is_open = False
        self.shop_is_open = False
        self.file_menu_open = False
        self.xp_timer = 0.0
        self.feedback_message = ""
        self.hover_text = ""
        self.ui_hover_text = ""
        self.shop_stock: list[dict[str, object]] = []
        self.quest_objective_text = ""
        self.quest_objective_completed = False
        self.quantity_mode = "all"
        self.chat_messages: list[str] = []
        self.chat_scroll = 0
        self.context_buttons: list[DirectButton] = []

        self.stats_panel = _panel((-0.02, 0.49, -0.22, 0.04), (-1.75, 0, 0.95), PANEL)
        self.stats = _text(self.stats_panel, "", (0.025, -0.035), STATS_TEXT_SCALE, TextNode.ALeft, TEXT, True)
        self.file_button = _button(self.stats_panel, "File", (0.37, 0, -0.155), SMALL_BUTTON_TEXT_SCALE, self.toggle_file_menu)
        self.file_menu = _panel((-0.11, 0.11, -0.155, 0.02), (0.37, 0, -0.21), PANEL_DARK, self.stats_panel)
        _button(self.file_menu, "Save", (0.0, 0, -0.025), SMALL_BUTTON_TEXT_SCALE, self._save_from_menu)
        _button(self.file_menu, "Load", (0.0, 0, -0.080), SMALL_BUTTON_TEXT_SCALE, self._load_from_menu)
        _button(self.file_menu, "Quit", (0.0, 0, -0.135), SMALL_BUTTON_TEXT_SCALE, self._quit_from_menu)
        self.file_menu.hide()

        self.feedback_panel = _panel((-0.54, 0.54, -0.075, 0.045), (0.0, 0, 0.91), PANEL_DARK)
        self.feedback = _text(self.feedback_panel, "", (0.0, -0.012), FEEDBACK_TEXT_SCALE, TextNode.ACenter, GOLD, True)
        self.progress_track = _frame((-0.48, 0.48, -0.058, -0.046), (0.0, 0, 0.0), SLOT, self.feedback_panel)
        self.progress_fill = _frame((-0.48, -0.48, -0.058, -0.046), (0.0, 0, 0.0), GOLD, self.feedback_panel)
        self.progress_track.hide()
        self.progress_fill.hide()
        self.xp_toast = _text(self.feedback_panel, "", (0.0, 0.070), FEEDBACK_TEXT_SCALE, TextNode.ACenter, GOLD, True)
        self.xp_toast.hide()

        self.quest_panel = _panel((-0.44, 0.44, -0.040, 0.040), (0.0, 0, 0.805), PANEL_DARK)
        self.quest_objective = _text(self.quest_panel, "", (0.0, -0.011), 0.030, TextNode.ACenter, TEXT, True)
        self.quest_panel.hide()

        self.chat_panel = _panel((-0.92, 0.40, -0.23, 0.03), (-0.76, 0, -0.70), PANEL_DARK)
        self.chat_lines = [
            _text(self.chat_panel, "", (-0.88, -0.010 - index * 0.031), CHAT_TEXT_SCALE, TextNode.ALeft, TEXT, True)
            for index in range(CHAT_VISIBLE_LINES)
        ]
        self.chat_up_button = _button(self.chat_panel, "Up", (0.30, 0, -0.050), SMALL_BUTTON_TEXT_SCALE, lambda: self.scroll_chat(1))
        self.chat_down_button = _button(self.chat_panel, "Down", (0.30, 0, -0.145), SMALL_BUTTON_TEXT_SCALE, lambda: self.scroll_chat(-1))

        self.side_panel = _panel((-0.26, 0.26, -1.38, 0.18), (1.48, 0, 0.74), PANEL)
        _text(self.side_panel, "Hearthvale", (0.0, 0.115), 0.034, TextNode.ACenter, GOLD)

        self.minimap = _panel((-0.18, 0.18, -0.18, 0.18), (0.0, 0, -0.08), PANEL_LIGHT, self.side_panel)
        _text(self.minimap, "N", (0.0, 0.135), 0.025, TextNode.ACenter, PANEL_DARK)
        _frame((-0.016, 0.016, -0.016, 0.016), (0.0, 0, 0.0), (0.88, 0.26, 0.16, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (-0.08, 0, -0.04), (0.14, 0.32, 0.76, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (0.10, 0, 0.06), (0.10, 0.44, 0.14, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (0.12, 0, -0.08), (0.68, 0.44, 0.20, 1), self.minimap)

        self.active_tab = INVENTORY_TAB
        self.tab_buttons: dict[str, DirectButton] = {}
        self.tab_frames: dict[str, DirectFrame] = {}
        self.inventory_slots: list[_InventorySlot] = []
        self.equipment_slots: dict[str, _EquipmentSlot] = {}
        self.skill_rows: dict[str, _SkillRow] = {}
        self._build_side_tabs()
        self.select_tab(INVENTORY_TAB)

        self.bank_panel = _panel((-0.86, 0.86, -0.68, 0.58), (0.0, 0, 0.02), PANEL)
        _text(self.bank_panel, "Bank", (0.0, 0.51), 0.045, TextNode.ACenter, GOLD)
        _button(self.bank_panel, "Close", (0.68, 0, 0.50), 0.040, self.on_bank_close)
        _button(self.bank_panel, "Deposit all", (-0.64, 0, 0.50), 0.035, self.on_deposit_all)
        self._build_quantity_buttons(self.bank_panel, (-0.28, 0.50))
        _text(self.bank_panel, "Item", (-0.80, 0.43), 0.022, TextNode.ALeft, GOLD)
        _text(self.bank_panel, "Inv/Bank", (-0.28, 0.43), 0.022, TextNode.ACenter, GOLD)
        _text(self.bank_panel, "Item", (0.06, 0.43), 0.022, TextNode.ALeft, GOLD)
        _text(self.bank_panel, "Inv/Bank", (0.58, 0.43), 0.022, TextNode.ACenter, GOLD)
        self.empty_bank_label = _text(self.bank_panel, "Bank is empty", (0.0, 0.18), 0.030, TextNode.ACenter, MUTED_TEXT)
        self.bank_rows: dict[str, _BankRow] = {}
        self.bank_panel.hide()

        self.shop_panel = _panel((-0.76, 0.76, -0.56, 0.50), (0.0, 0, 0.04), PANEL)
        _text(self.shop_panel, "General Store", (0.0, 0.43), 0.042, TextNode.ACenter, GOLD)
        _button(self.shop_panel, "Close", (0.58, 0, 0.42), 0.036, self.on_shop_close)
        _button(self.shop_panel, "Sell all", (-0.58, 0, 0.42), 0.030, self.on_sell_all)
        self._build_quantity_buttons(self.shop_panel, (-0.28, 0.42))
        self.shop_coin_label = _text(self.shop_panel, "", (0.0, 0.365), 0.024, TextNode.ACenter, GOLD, True)
        _text(self.shop_panel, "Item", (-0.68, 0.34), 0.022, TextNode.ALeft, GOLD)
        _text(self.shop_panel, "Owned", (0.20, 0.34), 0.022, TextNode.ACenter, GOLD)
        _text(self.shop_panel, "Price", (0.36, 0.34), 0.022, TextNode.ACenter, GOLD)
        self.empty_shop_label = _text(self.shop_panel, "No stock available", (0.0, 0.12), 0.030, TextNode.ACenter, MUTED_TEXT)
        self.shop_rows: dict[str, _ShopRow] = {}
        self.shop_panel.hide()

        self.context_panel = _panel((-0.17, 0.17, -0.30, 0.03), (0.0, 0, 0.0), PANEL_DARK)
        self.context_panel.hide()

    def update(
        self,
        *,
        account: str,
        time_text: str,
        inventory: dict[str, int],
        bank: dict[str, int],
        skills: Any,
        equipment: dict[str, str] | None = None,
        selected_text: str = "",
        selected_item_id: str | None = None,
        shop_stock: list[dict[str, object]] | None = None,
        gather_progress: float | None = None,
        quest_objective_text: str = "",
        quest_objective_completed: bool = False,
    ) -> None:
        if shop_stock is not None:
            self.shop_stock = list(shop_stock)
        self.stats.setText(
            "\n".join(
                [
                    f"Account: {account}",
                    time_text,
                ]
            )
        )
        self._sync_inventory_slots(inventory, selected_item_id)
        self._sync_equipment_slots(equipment or {})
        self._sync_skill_labels(skills)

        self._sync_bank_rows(inventory, bank)
        self._sync_shop_rows(inventory, self.shop_stock)
        self._sync_progress(gather_progress)
        self._sync_quest_objective(quest_objective_text, quest_objective_completed)

    def set_feedback(self, message: str) -> None:
        self.feedback_message = message
        self.add_chat_message(message)
        self._sync_feedback_text()
        xp_text = _xp_toast_text(message)
        if xp_text:
            self.xp_toast.setText(xp_text)
            self.xp_toast.show()
            self.xp_timer = 2.2

    def add_chat_message(self, message: str) -> None:
        message = message.strip()
        if not message:
            return
        follow_latest = self.chat_scroll == 0
        self.chat_messages.append(message)
        if len(self.chat_messages) > CHAT_HISTORY_LIMIT:
            overflow = len(self.chat_messages) - CHAT_HISTORY_LIMIT
            del self.chat_messages[:overflow]
        if follow_latest:
            self.chat_scroll = 0
        else:
            self.chat_scroll = min(self.chat_scroll + 1, self._max_chat_scroll())
        self._sync_chat_lines()

    def scroll_chat(self, delta: int) -> None:
        if delta == 0:
            return
        self.chat_scroll = max(0, min(self._max_chat_scroll(), self.chat_scroll + delta))
        self._sync_chat_lines()

    def set_hover_text(self, message: str) -> None:
        self.hover_text = message
        self._sync_feedback_text()

    def set_ui_hover_text(self, message: str) -> None:
        self.ui_hover_text = message
        self._sync_feedback_text()

    def tick(self, dt: float) -> None:
        if self.xp_timer <= 0:
            return
        self.xp_timer = max(0.0, self.xp_timer - dt)
        if self.xp_timer == 0:
            self.xp_toast.hide()

    def toggle_file_menu(self) -> None:
        self.file_menu_open = not self.file_menu_open
        if self.file_menu_open:
            self.file_menu.show()
        else:
            self.file_menu.hide()

    def _save_from_menu(self) -> None:
        self._close_file_menu()
        self.on_save()

    def _load_from_menu(self) -> None:
        self._close_file_menu()
        self.on_load()

    def _quit_from_menu(self) -> None:
        self._close_file_menu()
        self.on_quit()

    def open_bank(self) -> None:
        self.bank_is_open = True
        self.bank_panel.show()

    def close_bank(self) -> None:
        self.bank_is_open = False
        self.bank_panel.hide()

    def open_shop(self) -> None:
        self.shop_is_open = True
        self.shop_panel.show()

    def close_shop(self) -> None:
        self.shop_is_open = False
        self.shop_panel.hide()

    def show_context_menu(
        self,
        actions: list[tuple[str, str]],
        command: Callable[[str], None],
        pos: tuple[float, float, float] = (0.0, 0, 0.20),
    ) -> None:
        self.hide_context_menu()
        if not actions:
            return
        self.context_panel.setPos(*_clamp_context_menu_pos(pos))
        self.context_panel.show()
        for index, (action_id, label) in enumerate(actions[:9]):
            button = _button(
                self.context_panel,
                label,
                (0.0, 0, -0.035 - index * 0.055),
                0.023,
                lambda action_id=action_id: self._choose_context_action(action_id, command),
            )
            self.context_buttons.append(button)

    def hide_context_menu(self) -> None:
        for button in self.context_buttons:
            button.destroy()
        self.context_buttons.clear()
        if hasattr(self, "context_panel"):
            self.context_panel.hide()

    def _choose_context_action(self, action_id: str, command: Callable[[str], None]) -> None:
        self.hide_context_menu()
        command(action_id)

    def _close_file_menu(self) -> None:
        self.file_menu_open = False
        self.file_menu.hide()

    def select_tab(self, tab_id: str) -> None:
        if tab_id not in self.tab_frames:
            return
        self.set_ui_hover_text("")
        self.active_tab = tab_id
        for candidate_id, frame in self.tab_frames.items():
            if candidate_id == tab_id:
                frame.show()
            else:
                frame.hide()
        for candidate_id, button in self.tab_buttons.items():
            active = candidate_id == tab_id
            button["frameColor"] = (
                SLOT_HILITE if active else BUTTON,
                BUTTON_HOVER,
                BUTTON_HOVER,
                SLOT_HILITE if active else BUTTON,
            )
            button["text_fg"] = TEXT if active else MUTED_TEXT

    def _build_side_tabs(self) -> None:
        tab_labels = {
            INVENTORY_TAB: "Inventory",
            CLOTHES_TAB: "Clothes",
            SKILLS_TAB: "Skills",
        }
        tab_positions = {
            INVENTORY_TAB: -0.16,
            CLOTHES_TAB: 0.0,
            SKILLS_TAB: 0.16,
        }
        for tab_id in TAB_ORDER:
            self.tab_buttons[tab_id] = _button(
                self.side_panel,
                tab_labels[tab_id],
                (tab_positions[tab_id], 0, -0.32),
                SIDE_TAB_TEXT_SCALE,
                lambda tab_id=tab_id: self.select_tab(tab_id),
            )

        self.tab_box = _panel((-0.235, 0.235, -0.94, 0.04), (0.0, 0, -0.40), PANEL_DARK, self.side_panel)
        for tab_id in TAB_ORDER:
            self.tab_frames[tab_id] = _frame((-0.225, 0.225, -0.925, 0.025), (0.0, 0, 0.0), UI.TRANSPARENT, self.tab_box)

        self._build_inventory_tab(self.tab_frames[INVENTORY_TAB])
        self._build_clothes_tab(self.tab_frames[CLOTHES_TAB])
        self._build_skills_tab(self.tab_frames[SKILLS_TAB])

    def _build_quantity_buttons(self, parent: DirectFrame, origin: tuple[float, float]) -> None:
        x, z = origin
        _text(parent, "Qty", (x - 0.10, z - 0.004), SMALL_BUTTON_TEXT_SCALE, TextNode.ACenter, GOLD)
        for index, mode in enumerate(("1", "5", "10", "all")):
            label = "All" if mode == "all" else mode
            _button(parent, label, (x + index * 0.095, 0, z), SMALL_BUTTON_TEXT_SCALE, lambda mode=mode: self.set_quantity_mode(mode))

    def set_quantity_mode(self, mode: str) -> None:
        if mode in {"1", "5", "10", "all"}:
            self.quantity_mode = mode

    def transaction_quantity(self, available: int) -> int:
        if available <= 0:
            return 0
        if self.quantity_mode == "all":
            return available
        return min(available, int(self.quantity_mode))

    def _build_inventory_tab(self, parent: DirectFrame) -> None:
        x_start = -0.156
        z_start = -0.055
        x_gap = 0.104
        z_gap = 0.112
        for index in range(INVENTORY_SLOT_COUNT):
            col = index % INVENTORY_COLUMNS
            row = index // INVENTORY_COLUMNS
            button = _slot_button(
                parent,
                (x_start + col * x_gap, 0, z_start - row * z_gap),
                lambda index=index: self._select_inventory_slot(index),
            )
            self.inventory_slots.append(
                _InventorySlot(
                    button=button,
                    icon=_SlotIcon.create(button),
                    on_hover=self.set_ui_hover_text,
                )
            )

    def _build_clothes_tab(self, parent: DirectFrame) -> None:
        _frame((-0.044, 0.044, -0.18, 0.18), (0.0, 0, -0.36), (0.20, 0.13, 0.08, 1.0), parent)
        _frame((-0.030, 0.030, -0.055, 0.005), (0.0, 0, -0.16), (0.64, 0.46, 0.26, 1.0), parent)
        _frame((-0.030, 0.030, -0.040, 0.040), (0.0, 0, -0.55), (0.38, 0.24, 0.12, 1.0), parent)
        for slot_id, label, x, z in EQUIPMENT_SLOT_LAYOUT:
            button = _slot_button(
                parent,
                (x, 0, z),
                lambda slot_id=slot_id: self.on_unequip_slot(slot_id),
            )
            equipment_slot = _EquipmentSlot(button=button, empty_label=label)
            equipment_slot.clear()
            self.equipment_slots[slot_id] = equipment_slot

    def _build_skills_tab(self, parent: DirectFrame) -> None:
        for index, skill_id in enumerate(self.skill_ids):
            z = -0.075 - index * SKILL_ROW_SPACING
            _skill_icon(parent, skill_id, (-0.178, 0, z - 0.010))
            self.skill_rows[skill_id] = _SkillRow(
                name_label=_text(
                    parent,
                    "",
                    (-0.125, z + 0.018),
                    SKILL_NAME_TEXT_SCALE,
                    TextNode.ALeft,
                    TEXT,
                    True,
                ),
                detail_label=_text(
                    parent,
                    "",
                    (-0.125, z - 0.020),
                    SKILL_DETAIL_TEXT_SCALE,
                    TextNode.ALeft,
                    MUTED_TEXT,
                    True,
                ),
            )

    def _select_inventory_slot(self, index: int) -> None:
        if index < 0 or index >= len(self.inventory_slots):
            return
        item_id = self.inventory_slots[index].item_id
        if item_id is not None:
            self.on_select_item(item_id)

    def _sync_inventory_slots(self, inventory: dict[str, int], selected_item_id: str | None) -> None:
        visible_item_ids = _inventory_item_ids(self.items_data, inventory)[:INVENTORY_SLOT_COUNT]
        for index, slot in enumerate(self.inventory_slots):
            if index < len(visible_item_ids):
                item_id = visible_item_ids[index]
                slot.set_item(
                    self.items_data,
                    item_id,
                    inventory.get(item_id, 0),
                    item_id == selected_item_id,
                )
            else:
                slot.clear()

    def _sync_equipment_slots(self, equipment: dict[str, str]) -> None:
        for slot_id, slot in self.equipment_slots.items():
            item_id = equipment.get(slot_id)
            if item_id:
                slot.set_item(_equipment_slot_text(self.items_data, item_id))
            else:
                slot.clear()

    def _sync_skill_labels(self, skills: Any) -> None:
        for skill_id, row in self.skill_rows.items():
            row.set_skill(_skill_label(self.skills_data, skill_id), skills.get(skill_id))

    def _sync_feedback_text(self) -> None:
        self.feedback.setText(self.ui_hover_text or self.hover_text or self.feedback_message)

    def _sync_chat_lines(self) -> None:
        visible_messages = self._visible_chat_messages()
        for index, line in enumerate(self.chat_lines):
            text = visible_messages[index] if index < len(visible_messages) else ""
            line.setText(text)

    def _visible_chat_messages(self) -> list[str]:
        if len(self.chat_messages) <= CHAT_VISIBLE_LINES:
            return list(self.chat_messages)
        start = len(self.chat_messages) - CHAT_VISIBLE_LINES - self.chat_scroll
        start = max(0, min(start, len(self.chat_messages) - CHAT_VISIBLE_LINES))
        return self.chat_messages[start : start + CHAT_VISIBLE_LINES]

    def _max_chat_scroll(self) -> int:
        return max(0, len(self.chat_messages) - CHAT_VISIBLE_LINES)

    def _sync_quest_objective(self, text: str, completed: bool) -> None:
        self.quest_objective_text = text
        self.quest_objective_completed = completed
        if not text:
            self.quest_panel.hide()
            self.quest_objective.setText("")
            return
        self.quest_panel.show()
        self.quest_objective.setText(text)
        self.quest_objective["fg"] = GOLD if completed else TEXT

    def _sync_bank_rows(self, inventory: dict[str, int], bank: dict[str, int]) -> None:
        visible_item_ids = _bank_item_ids(self.items_data, inventory, bank)
        visible_item_id_set = set(visible_item_ids)

        for item_id in list(self.bank_rows):
            if item_id not in visible_item_id_set:
                self.bank_rows.pop(item_id).destroy()

        if visible_item_ids:
            self.empty_bank_label.hide()
        else:
            self.empty_bank_label.show()

        rows_per_column = max(1, (len(visible_item_ids) + 1) // 2)
        for index, item_id in enumerate(visible_item_ids):
            col = index // rows_per_column
            row_index = index % rows_per_column
            x = -0.80 if col == 0 else 0.06
            y = 0.36 - row_index * 0.052
            row = self.bank_rows.get(item_id)
            if row is None:
                row = _BankRow(
                    item_label=_text(self.bank_panel, _item_name(self.items_data, item_id), (x, y), ROW_TEXT_SCALE, TextNode.ALeft, TEXT, True),
                    bank_label=_text(self.bank_panel, "", (x + 0.52, y), ROW_TEXT_SCALE, TextNode.ACenter, TEXT, True),
                    deposit_button=_button(
                        self.bank_panel,
                        "Dep",
                        (x + 0.64, 0, y + 0.004),
                        ROW_BUTTON_TEXT_SCALE,
                        lambda item_id=item_id: self.on_deposit_item(item_id),
                    ),
                    withdraw_button=_button(
                        self.bank_panel,
                        "Wit",
                        (x + 0.77, 0, y + 0.004),
                        ROW_BUTTON_TEXT_SCALE,
                        lambda item_id=item_id: self.on_withdraw_item(item_id),
                    ),
                )
                self.bank_rows[item_id] = row
            row.set_pos(x, y)
            row.bank_label.setText(f"{inventory.get(item_id, 0)}/{bank.get(item_id, 0)}")

    def _sync_shop_rows(self, inventory: dict[str, int], shop_stock: list[dict[str, object]]) -> None:
        self.shop_coin_label.setText(f"Coins: {inventory.get(COINS_ITEM_ID, 0)}")
        stock_prices = _stock_prices(shop_stock)
        buy_item_ids = sorted(stock_prices, key=lambda item_id: (_category_sort_key(self.items_data, item_id), item_id))
        sell_item_ids = [
            item_id
            for item_id in _sellable_item_ids(self.items_data, inventory)
            if item_id not in stock_prices and item_id != COINS_ITEM_ID
        ]
        visible_rows = [(item_id, item_id, "buy") for item_id in buy_item_ids]
        visible_rows.extend((f"sell:{item_id}", item_id, "sell") for item_id in sell_item_ids)
        visible_row_ids = {row_id for row_id, _item_id, _mode in visible_rows}

        for item_id in list(self.shop_rows):
            if item_id not in visible_row_ids:
                self.shop_rows.pop(item_id).destroy()

        if visible_rows:
            self.empty_shop_label.hide()
        else:
            self.empty_shop_label.show()

        for index, (row_id, item_id, mode) in enumerate(visible_rows):
            y = 0.27 - index * 0.052
            row = self.shop_rows.get(row_id)
            if row is None:
                action_text = "Buy" if mode == "buy" else "Sell"
                command = (
                    (lambda item_id=item_id: self.on_buy_item(item_id))
                    if mode == "buy"
                    else (lambda item_id=item_id: self.on_sell_item(item_id))
                )
                row = _ShopRow(
                    item_label=_text(self.shop_panel, _item_name(self.items_data, item_id), (-0.68, y), ROW_TEXT_SCALE, TextNode.ALeft, TEXT, True),
                    quantity_label=_text(self.shop_panel, "", (0.20, y), ROW_TEXT_SCALE, TextNode.ACenter, TEXT, True),
                    price_label=_text(self.shop_panel, "", (0.36, y), ROW_TEXT_SCALE, TextNode.ACenter, TEXT, True),
                    action_button=_button(
                        self.shop_panel,
                        action_text,
                        (0.58, 0, y + 0.004),
                        ROW_BUTTON_TEXT_SCALE,
                        command,
                    ),
                )
                self.shop_rows[row_id] = row
            row.set_pos(y)
            row.quantity_label.setText(str(inventory.get(item_id, 0)))
            row.price_label.setText(str(stock_prices[item_id] if mode == "buy" else _sell_price(self.items_data, item_id)))

    def _sync_progress(self, gather_progress: float | None) -> None:
        if gather_progress is None:
            self.progress_track.hide()
            self.progress_fill.hide()
            return
        progress = max(0.0, min(1.0, gather_progress))
        self.progress_track.show()
        self.progress_fill.show()
        self.progress_fill["frameSize"] = (-0.48, -0.48 + 0.96 * progress, -0.058, -0.046)


@dataclass
class _InventorySlot:
    button: DirectButton
    icon: "_SlotIcon"
    on_hover: Callable[[str], None]
    item_id: str | None = None
    hover_text: str = ""
    is_hovered: bool = False

    def __post_init__(self) -> None:
        self.button.bind(DGG.ENTER, self._on_hover_enter)
        self.button.bind(DGG.EXIT, self._on_hover_exit)

    def set_item(
        self,
        items_data: dict[str, dict[str, object]],
        item_id: str,
        quantity: int,
        selected: bool,
    ) -> None:
        if quantity <= 0:
            self.clear()
            return
        self.item_id = item_id
        self.hover_text = _inventory_hover_text(items_data, item_id, quantity)
        base_color = SLOT_HILITE if selected else SLOT
        hover_color = SLOT_HILITE if selected else BUTTON_HOVER
        self.button["text"] = _format_quantity(quantity)
        self.button["text_fg"] = TEXT
        self.button["frameColor"] = (base_color, hover_color, hover_color, base_color)
        self.icon.set_item(items_data, item_id)
        if self.is_hovered:
            self.on_hover(self.hover_text)

    def clear(self) -> None:
        self.item_id = None
        self.hover_text = ""
        self.button["text"] = ""
        self.button["text_fg"] = MUTED_TEXT
        self.button["frameColor"] = (SLOT, SLOT, SLOT, SLOT)
        self.icon.clear()
        if self.is_hovered:
            self.on_hover("")

    def _on_hover_enter(self, _event: Any = None) -> None:
        self.is_hovered = True
        if self.hover_text:
            self.on_hover(self.hover_text)

    def _on_hover_exit(self, _event: Any = None) -> None:
        self.is_hovered = False
        self.on_hover("")


@dataclass
class _SlotIcon:
    parts: list[DirectFrame]
    label: OnscreenText

    @classmethod
    def create(cls, parent: Any) -> "_SlotIcon":
        icon = cls(
            parts=[
                _icon_frame((0.0, 0.0, 0.0, 0.0), (0.0, 0, 0.0), UI.TRANSPARENT, parent)
                for _ in range(5)
            ],
            label=_icon_label(parent),
        )
        icon.clear()
        return icon

    def set_item(self, items_data: dict[str, dict[str, object]], item_id: str) -> None:
        specs = _item_icon_specs(items_data, item_id)
        self.label.setText(_item_icon_label(items_data, item_id))
        self.label.show()
        for index, part in enumerate(self.parts):
            if index < len(specs):
                frame_size, pos, color = specs[index]
                part["frameSize"] = frame_size
                part["pos"] = pos
                part["frameColor"] = color
                part.show()
            else:
                part.hide()

    def clear(self) -> None:
        for part in self.parts:
            part.hide()
        self.label.setText("")
        self.label.hide()


@dataclass
class _EquipmentSlot:
    button: DirectButton
    empty_label: str

    def set_item(self, text: str) -> None:
        self.button["text"] = text
        self.button["text_fg"] = TEXT
        self.button["frameColor"] = (SLOT_HILITE, BUTTON_HOVER, BUTTON_HOVER, SLOT_HILITE)

    def clear(self) -> None:
        self.button["text"] = self.empty_label
        self.button["text_fg"] = MUTED_TEXT
        self.button["frameColor"] = (SLOT, SLOT, SLOT, SLOT)


@dataclass
class _SkillRow:
    name_label: OnscreenText
    detail_label: OnscreenText

    def set_skill(self, label: str, state: Any) -> None:
        self.name_label.setText(_skill_name_text(label))
        self.detail_label.setText(_skill_detail_text(state))


@dataclass
class _BankRow:
    item_label: OnscreenText
    bank_label: OnscreenText
    deposit_button: DirectButton
    withdraw_button: DirectButton

    def set_pos(self, x: float, y: float) -> None:
        self.item_label.setPos(x, y)
        self.bank_label.setPos(x + 0.52, y)
        self.deposit_button.setPos(x + 0.64, 0, y + 0.004)
        self.withdraw_button.setPos(x + 0.77, 0, y + 0.004)

    def destroy(self) -> None:
        self.item_label.destroy()
        self.bank_label.destroy()
        self.deposit_button.destroy()
        self.withdraw_button.destroy()


@dataclass
class _ShopRow:
    item_label: OnscreenText
    quantity_label: OnscreenText
    price_label: OnscreenText
    action_button: DirectButton

    def set_pos(self, y: float) -> None:
        self.item_label.setPos(-0.68, y)
        self.quantity_label.setPos(0.20, y)
        self.price_label.setPos(0.36, y)
        self.action_button.setPos(0.58, 0, y + 0.004)

    def destroy(self) -> None:
        self.item_label.destroy()
        self.quantity_label.destroy()
        self.price_label.destroy()
        self.action_button.destroy()


def _frame(
    frame_size: tuple[float, float, float, float],
    pos: tuple[float, float, float],
    color: tuple[float, float, float, float],
    parent: Any | None = None,
) -> DirectFrame:
    kwargs: dict[str, Any] = {"frameSize": frame_size, "frameColor": color}
    if parent is not None:
        kwargs["parent"] = parent
    frame = DirectFrame(**kwargs)
    frame.setPos(*pos)
    return frame


def _icon_frame(
    frame_size: tuple[float, float, float, float],
    pos: tuple[float, float, float],
    color: tuple[float, float, float, float],
    parent: Any,
) -> DirectFrame:
    frame = DirectFrame(
        parent=parent,
        frameSize=frame_size,
        frameColor=color,
        state=DGG.DISABLED,
    )
    frame.setPos(*pos)
    return frame


def _icon_label(parent: Any) -> OnscreenText:
    return OnscreenText(
        parent=parent,
        text="",
        pos=(0.0, -0.014),
        scale=ITEM_ICON_LABEL_TEXT_SCALE,
        align=TextNode.ACenter,
        fg=TEXT,
        mayChange=True,
        shadow=(0.02, 0.01, 0.0, 1.0),
        shadowOffset=(0.045, -0.045),
    )


def _panel(
    frame_size: tuple[float, float, float, float],
    pos: tuple[float, float, float],
    color: tuple[float, float, float, float],
    parent: Any | None = None,
    *,
    border: float = 0.012,
) -> DirectFrame:
    panel = _frame(frame_size, pos, UI.STONE, parent)
    left, right, bottom, top = frame_size
    _frame((left + border, right - border, bottom + border, top - border), (0, 0, 0), color, panel)
    return panel


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


def _clamp_context_menu_pos(pos: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = pos
    return (max(-1.24, min(1.24, x)), y, max(-0.62, min(0.88, z)))


def _slot_button(parent: Any, pos: tuple[float, float, float], command: Callable[[], None]) -> DirectButton:
    return DirectButton(
        parent=parent,
        pos=pos,
        frameSize=(-0.045, 0.045, -0.045, 0.045),
        frameColor=(SLOT, SLOT, SLOT, SLOT),
        text="",
        text_align=TextNode.ARight,
        text_fg=MUTED_TEXT,
        text_pos=(0.037, -0.038),
        text_scale=INVENTORY_QUANTITY_TEXT_SCALE,
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


def _skill_icon(parent: Any, skill_id: str, pos: tuple[float, float, float]) -> None:
    color = {
        "woodcutting": (0.42, 0.25, 0.10, 1.0),
        "mining": (0.52, 0.52, 0.48, 1.0),
        "fishing": (0.25, 0.48, 0.64, 1.0),
        "cooking": (0.72, 0.36, 0.18, 1.0),
        "attack": (0.62, 0.18, 0.14, 1.0),
        "strength": (0.72, 0.48, 0.18, 1.0),
        "defence": (0.26, 0.34, 0.68, 1.0),
        "hitpoints": (0.72, 0.12, 0.18, 1.0),
        "smithing": (0.42, 0.42, 0.38, 1.0),
    }.get(skill_id, SLOT_HILITE)
    _frame((-0.026, 0.026, -0.026, 0.026), pos, SLOT, parent)
    _frame((-0.017, 0.017, -0.017, 0.017), pos, color, parent)


def _skill_name_text(label: str) -> str:
    words = label.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words) if words else label


def _skill_detail_text(state: Any) -> str:
    return f"Level {state.level}  {state.xp} XP"


def _item_name(items_data: dict[str, dict[str, object]], item_id: str) -> str:
    return str(items_data.get(item_id, {}).get("name") or item_id.replace("_", " "))


def _inventory_hover_text(items_data: dict[str, dict[str, object]], item_id: str, quantity: int) -> str:
    name = _item_name(items_data, item_id)
    return name if quantity == 1 else f"{name} x{quantity}"


def _item_icon_label(items_data: dict[str, dict[str, object]], item_id: str) -> str:
    definition = items_data.get(item_id, {})
    category = str(definition.get("category") or "")
    name = _item_name(items_data, item_id).lower()
    tool_for = str(definition.get("tool_for") or "")

    if category == "currency":
        return "$"
    if category == "tool":
        if tool_for == "woodcutting" or "axe" in item_id:
            return "AXE"
        if tool_for == "mining" or "pickaxe" in item_id:
            return "PICK"
        if "rod" in item_id:
            return "ROD"
        if "net" in item_id:
            return "NET"
        if tool_for == "cooking" or "pot" in item_id:
            return "POT"
        return "TOOL"
    if category == "weapon":
        return "SWD"
    if category == "armor":
        return "SHD"
    if category == "wood":
        return "LOG"
    if category == "ore":
        return "ORE"
    if category == "bar":
        return "BAR"
    if category == "fish":
        return "FISH"
    return _abbreviated_item_label(name)


def _abbreviated_item_label(name: str) -> str:
    words = [word for word in name.replace("_", " ").split() if word]
    if not words:
        return "ITEM"
    if len(words) == 1:
        return words[0][:4].upper()
    return "".join(word[0] for word in words[:4]).upper()


def _equipment_slot_text(items_data: dict[str, dict[str, object]], item_id: str) -> str:
    words = _item_name(items_data, item_id).split()
    if not words:
        words = [item_id]
    return "\n".join(_slot_word(word) for word in words[:2])


def _item_icon_specs(
    items_data: dict[str, dict[str, object]],
    item_id: str,
) -> list[IconSpec]:
    definition = items_data.get(item_id, {})
    category = str(definition.get("category") or "")
    name = _item_name(items_data, item_id).lower()
    if category == "currency":
        return _coin_icon_specs()
    if category == "tool":
        return _tool_icon_specs(item_id)
    if category == "weapon":
        return _weapon_icon_specs(item_id)
    if category == "armor":
        return _shield_icon_specs(item_id)
    if category == "wood":
        return _wood_icon_specs(item_id)
    if category == "ore":
        return _ore_icon_specs(item_id)
    if category == "bar":
        return _bar_icon_specs(item_id)
    if category == "fish":
        return _fish_icon_specs(name)
    return _generic_icon_specs()


def _coin_icon_specs() -> list[IconSpec]:
    return [
        ((-0.022, 0.018, -0.006, 0.006), (-0.002, 0, 0.021), (0.74, 0.48, 0.11, 1.0)),
        ((-0.022, 0.020, -0.006, 0.006), (0.004, 0, 0.011), GOLD),
        ((-0.020, 0.022, -0.006, 0.006), (-0.004, 0, 0.001), (0.94, 0.68, 0.20, 1.0)),
        ((-0.010, 0.012, -0.002, 0.002), (0.002, 0, 0.012), (1.0, 0.90, 0.45, 1.0)),
    ]


def _tool_icon_specs(item_id: str) -> list[IconSpec]:
    wood = (0.54, 0.30, 0.12, 1.0)
    metal = (0.72, 0.66, 0.54, 1.0)
    dark_metal = (0.36, 0.35, 0.32, 1.0)
    if "fishing" in item_id:
        return [
            ((-0.004, 0.004, -0.025, 0.026), (-0.005, 0, 0.011), wood),
            ((-0.012, 0.012, -0.003, 0.003), (0.010, 0, 0.032), metal),
            ((-0.006, 0.006, -0.003, 0.003), (0.020, 0, -0.013), (0.70, 0.82, 0.88, 1.0)),
        ]
    if "pickaxe" in item_id:
        return [
            ((-0.004, 0.004, -0.024, 0.024), (0.000, 0, 0.007), wood),
            ((-0.030, 0.030, -0.006, 0.006), (0.000, 0, 0.028), metal),
            ((-0.020, -0.008, -0.010, 0.010), (-0.008, 0, 0.022), dark_metal),
            ((0.008, 0.020, -0.010, 0.010), (0.008, 0, 0.022), dark_metal),
        ]
    return [
        ((-0.005, 0.005, -0.024, 0.026), (0.008, 0, 0.007), wood),
        ((-0.030, 0.006, -0.014, 0.014), (-0.009, 0, 0.030), metal),
        ((-0.026, -0.010, -0.008, 0.008), (-0.012, 0, 0.028), dark_metal),
    ]


def _weapon_icon_specs(item_id: str) -> list[IconSpec]:
    metal = _metal_color(item_id)
    return [
        ((-0.007, 0.007, -0.024, 0.025), (0.000, 0, 0.016), metal),
        ((-0.018, 0.018, -0.004, 0.004), (0.000, 0, -0.004), (0.62, 0.42, 0.17, 1.0)),
        ((-0.005, 0.005, -0.014, 0.006), (0.000, 0, -0.019), (0.36, 0.20, 0.08, 1.0)),
        ((-0.003, 0.003, -0.004, 0.006), (0.000, 0, 0.043), (0.95, 0.91, 0.76, 1.0)),
    ]


def _shield_icon_specs(item_id: str) -> list[IconSpec]:
    metal = _metal_color(item_id)
    return [
        ((-0.027, 0.027, -0.025, 0.025), (0.000, 0, 0.014), (0.20, 0.13, 0.07, 1.0)),
        ((-0.022, 0.022, -0.022, 0.022), (0.000, 0, 0.016), metal),
        ((-0.004, 0.004, -0.020, 0.020), (0.000, 0, 0.016), (0.95, 0.77, 0.32, 1.0)),
        ((-0.016, 0.016, -0.004, 0.004), (0.000, 0, 0.018), (0.95, 0.77, 0.32, 1.0)),
    ]


def _wood_icon_specs(item_id: str) -> list[IconSpec]:
    core = {
        "oak_logs": (0.58, 0.35, 0.14, 1.0),
        "willow_logs": (0.70, 0.54, 0.25, 1.0),
        "maple_logs": (0.72, 0.39, 0.16, 1.0),
        "yew_logs": (0.45, 0.29, 0.12, 1.0),
        "magic_logs": (0.45, 0.28, 0.68, 1.0),
        "redwood_logs": (0.62, 0.22, 0.13, 1.0),
    }.get(item_id, (0.54, 0.31, 0.13, 1.0))
    return [
        ((-0.030, 0.030, -0.015, 0.015), (0.000, 0, 0.014), (0.22, 0.12, 0.05, 1.0)),
        ((-0.026, 0.026, -0.010, 0.010), (0.000, 0, 0.016), core),
        ((-0.024, -0.017, -0.012, 0.012), (-0.002, 0, 0.016), (0.72, 0.54, 0.27, 1.0)),
        ((0.014, 0.020, -0.009, 0.009), (0.000, 0, 0.016), (0.25, 0.13, 0.05, 1.0)),
    ]


def _ore_icon_specs(item_id: str) -> list[IconSpec]:
    color = {
        "copper_ore": (0.76, 0.36, 0.16, 1.0),
        "iron_ore": (0.72, 0.62, 0.48, 1.0),
        "coal": (0.07, 0.07, 0.08, 1.0),
        "mithril_ore": (0.18, 0.60, 0.68, 1.0),
        "adamant_ore": (0.24, 0.68, 0.30, 1.0),
        "starsteel_ore": (0.35, 0.68, 0.92, 1.0),
    }.get(item_id, (0.52, 0.52, 0.48, 1.0))
    return [
        ((-0.026, 0.020, -0.020, 0.018), (-0.002, 0, 0.015), (0.18, 0.17, 0.15, 1.0)),
        ((-0.020, 0.024, -0.016, 0.020), (0.002, 0, 0.017), color),
        ((-0.010, 0.014, -0.007, 0.007), (0.000, 0, 0.026), (0.82, 0.80, 0.70, 0.65)),
        ((-0.020, -0.006, -0.006, 0.008), (-0.003, 0, 0.009), (0.06, 0.05, 0.04, 0.45)),
    ]


def _bar_icon_specs(item_id: str) -> list[IconSpec]:
    color = _metal_color(item_id.replace("_bar", "_sword"))
    return [
        ((-0.028, 0.028, -0.015, 0.015), (0.000, 0, 0.014), (0.16, 0.15, 0.14, 1.0)),
        ((-0.024, 0.024, -0.010, 0.010), (0.000, 0, 0.017), color),
        ((-0.016, 0.016, -0.003, 0.003), (0.000, 0, 0.024), (0.95, 0.88, 0.62, 0.55)),
    ]


def _fish_icon_specs(name: str) -> list[IconSpec]:
    cooked = name.startswith("cooked")
    body = (0.88, 0.58, 0.34, 1.0) if cooked else (0.42, 0.70, 0.78, 1.0)
    fin = (0.72, 0.36, 0.18, 1.0) if cooked else (0.22, 0.48, 0.62, 1.0)
    return [
        ((-0.026, 0.018, -0.013, 0.013), (-0.002, 0, 0.016), body),
        ((0.012, 0.028, -0.017, 0.017), (0.002, 0, 0.016), fin),
        ((-0.028, -0.018, -0.008, 0.008), (-0.002, 0, 0.016), (0.92, 0.78, 0.58, 1.0)),
        ((0.003, 0.008, 0.010, 0.020), (-0.002, 0, 0.014), fin),
        ((-0.020, -0.016, 0.004, 0.008), (0.000, 0, 0.016), (0.03, 0.04, 0.05, 1.0)),
    ]


def _generic_icon_specs() -> list[IconSpec]:
    return [
        ((-0.026, 0.026, -0.026, 0.026), (0.000, 0, 0.015), (0.20, 0.19, 0.18, 1.0)),
        ((-0.018, 0.018, -0.018, 0.018), (0.000, 0, 0.015), (0.58, 0.50, 0.34, 1.0)),
        ((-0.004, 0.004, -0.014, 0.014), (0.000, 0, 0.015), GOLD),
    ]


def _metal_color(item_id: str) -> tuple[float, float, float, float]:
    if item_id.startswith("iron"):
        return (0.72, 0.68, 0.58, 1.0)
    if item_id.startswith("mithril"):
        return (0.22, 0.62, 0.72, 1.0)
    if item_id.startswith("starsteel"):
        return (0.34, 0.68, 0.94, 1.0)
    return (0.74, 0.46, 0.22, 1.0)


def _slot_word(word: str) -> str:
    if len(word) <= 8:
        return word
    return f"{word[:7]}."


def _format_quantity(quantity: int) -> str:
    if quantity >= 1_000_000:
        return f"{quantity // 1_000_000}M"
    if quantity >= 10_000:
        return f"{quantity // 1_000}K"
    return str(quantity)


def _skill_ids(skills_data: dict[str, dict[str, object]]) -> list[str]:
    skill_ids = list(DEFAULT_SKILL_IDS)
    for skill_id in skills_data:
        if skill_id not in skill_ids:
            skill_ids.append(skill_id)
    return skill_ids


def _skill_label(skills_data: dict[str, dict[str, object]], skill_id: str) -> str:
    definition = skills_data.get(skill_id, {})
    return str(
        definition.get("display_name")
        or definition.get("name")
        or skill_id.replace("_", " ")
    )


def _xp_toast_text(message: str) -> str:
    if " XP" not in message or "+" not in message:
        return ""
    xp_parts = [part.strip() for part in message.split(",") if " XP" in part and "+" in part]
    if not xp_parts:
        return ""
    return xp_parts[-1]


def _bank_item_ids(
    items_data: dict[str, dict[str, object]],
    inventory: dict[str, int],
    bank: dict[str, int],
) -> list[str]:
    item_ids = {
        item_id
        for source in (inventory, bank)
        for item_id, quantity in source.items()
        if quantity > 0
    }
    return sorted(
        item_ids,
        key=lambda item_id: (_category_sort_key(items_data, item_id), item_id),
    )


def _inventory_item_ids(
    items_data: dict[str, dict[str, object]],
    inventory: dict[str, int],
) -> list[str]:
    item_ids = {
        item_id
        for item_id, quantity in inventory.items()
        if quantity > 0
    }
    return sorted(
        item_ids,
        key=lambda item_id: (_category_sort_key(items_data, item_id), item_id),
    )


def _sellable_item_ids(
    items_data: dict[str, dict[str, object]],
    inventory: dict[str, int],
) -> list[str]:
    item_ids = {
        item_id
        for item_id, quantity in inventory.items()
        if quantity > 0 and _sell_price(items_data, item_id) > 0
    }
    return sorted(
        item_ids,
        key=lambda item_id: (_category_sort_key(items_data, item_id), item_id),
    )


def _sell_price(items_data: dict[str, dict[str, object]], item_id: str) -> int:
    return int(items_data.get(item_id, {}).get("sell_price", 0))


def _stock_prices(shop_stock: list[dict[str, object]]) -> dict[str, int]:
    prices: dict[str, int] = {}
    for stock_item in shop_stock:
        item_id = stock_item.get("item_id")
        price = stock_item.get("price")
        if isinstance(item_id, str) and isinstance(price, int) and price > 0:
            prices[item_id] = price
    return prices


def _category_sort_key(items_data: dict[str, dict[str, object]], item_id: str) -> tuple[int, str]:
    category = str(items_data.get(item_id, {}).get("category") or "")
    return {
        "currency": 0,
        "tool": 1,
        "weapon": 2,
        "armor": 3,
        "wood": 4,
        "ore": 5,
        "bar": 6,
        "fish": 7,
        "misc": 8,
    }.get(category, 9), category
