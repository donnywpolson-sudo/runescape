from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from direct.gui.DirectGui import DGG, DirectButton, DirectEntry, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from game.style import UiPalette as UI
from game.systems.inventory import COINS_ITEM_ID, INVENTORY_SLOT_LIMIT, is_non_stackable_item

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
DEFAULT_VIEWPORT_ASPECT = 16.0 / 9.0
TAB_BOX_FRAME_SIZE = (-0.235, 0.235, -0.94, 0.04)
TAB_BOX_COLLAPSED_FRAME_SIZE = (-0.235, 0.235, -0.075, 0.04)
TAB_BOX_POS = (DEFAULT_VIEWPORT_ASPECT - TAB_BOX_FRAME_SIZE[1], 0, -1.0 - TAB_BOX_FRAME_SIZE[2])
TAB_BUTTON_FRAME_SIZE = (-0.070, 0.070, -0.033, 0.033)
INVENTORY_COLUMNS = 4
INVENTORY_ROWS = 7
INVENTORY_SLOT_COUNT = INVENTORY_SLOT_LIMIT
INVENTORY_QUANTITY_TEXT_SCALE = 0.027
SIDE_TAB_TEXT_SCALE = 0.024
SKILL_ROW_SPACING = 0.078
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
BANK_TITLE_TEXT_SCALE = 0.058
BANK_HEADER_TEXT_SCALE = 0.032
BANK_ROW_TEXT_SCALE = 0.030
BANK_ROW_BUTTON_TEXT_SCALE = 0.030
BANK_ROW_SPACING = 0.068
BANK_LEFT_COLUMN_X = -0.87
BANK_RIGHT_COLUMN_X = 0.04
IconSpec = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float],
    tuple[float, float, float, float],
] | tuple[
    tuple[float, float, float, float],
    tuple[float, float, float],
    tuple[float, float, float, float],
    float,
]
DEFAULT_SKILL_IDS = (
    "woodcutting",
    "mining",
    "fishing",
    "cooking",
    "attack",
    "strength",
    "defence",
    "ranged",
    "magic",
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
        world_data: dict[str, object] | None = None,
        recipes_data: dict[str, object] | None = None,
        *,
        on_bank_close: Callable[[], None] | None = None,
        on_deposit_item: Callable[[str], None] | None = None,
        on_withdraw_item: Callable[[str], None] | None = None,
        on_deposit_all: Callable[[], None] | None = None,
        on_shop_close: Callable[[], None] | None = None,
        on_buy_item: Callable[[str], None] | None = None,
        on_sell_item: Callable[[str], None] | None = None,
        on_sell_all: Callable[[], None] | None = None,
        on_select_item: Callable[[str, int], None] | None = None,
        on_examine_item: Callable[[str], None] | None = None,
        on_drop_item: Callable[[str], None] | None = None,
        on_unequip_slot: Callable[[str], None] | None = None,
        on_combat_style: Callable[[str], None] | None = None,
        on_save: Callable[[], None] | None = None,
        on_load: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ) -> None:
        self.items_data = items_data or {}
        self.skills_data = _skills_data or {}
        self.world_data = world_data or {}
        self.recipes_data = recipes_data or {}
        self.skill_ids = _skill_ids(self.skills_data)
        self.on_bank_close = on_bank_close or (lambda: None)
        self.on_deposit_item = on_deposit_item or (lambda _item_id: None)
        self.on_withdraw_item = on_withdraw_item or (lambda _item_id: None)
        self.on_deposit_all = on_deposit_all or (lambda: None)
        self.on_shop_close = on_shop_close or (lambda: None)
        self.on_buy_item = on_buy_item or (lambda _item_id: None)
        self.on_sell_item = on_sell_item or (lambda _item_id: None)
        self.on_sell_all = on_sell_all or (lambda: None)
        self.on_select_item = _select_item_callback(on_select_item)
        self.on_examine_item = on_examine_item or (lambda _item_id: None)
        self.on_drop_item = on_drop_item or (lambda _item_id: None)
        self.on_unequip_slot = on_unequip_slot or (lambda _slot: None)
        self.on_combat_style = on_combat_style or (lambda _style: None)
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
        self.shop_tab = "buy"
        self.shop_selected_row_id = ""
        self.shop_amount_context: tuple[str, str] | None = None
        self.quantity_context: tuple[str, str, int, Callable[[int], None]] | None = None
        self.chat_messages: list[str] = []
        self.chat_scroll = 0
        self.context_buttons: list[DirectButton] = []
        self.loot_buttons: list[DirectButton] = []
        self.loot_tile: tuple[int, int] | None = None
        self.loot_command: Callable[[str], None] | None = None
        self.viewport_aspect = DEFAULT_VIEWPORT_ASPECT

        self.stats_panel = _panel((-0.02, 0.49, -0.22, 0.04), (-1.75, 0, 0.95), PANEL)
        self.stats = _text(self.stats_panel, "", (0.025, -0.035), STATS_TEXT_SCALE, TextNode.ALeft, TEXT, True)
        self.file_button = _button(self.stats_panel, "File", (0.37, 0, -0.155), SMALL_BUTTON_TEXT_SCALE, self.toggle_file_menu)
        self.settings_button = _button(
            self.stats_panel,
            "Settings",
            (0.23, 0, -0.155),
            SMALL_BUTTON_TEXT_SCALE,
            self.toggle_settings_menu,
        )
        self.file_menu = _panel((-0.11, 0.11, -0.155, 0.02), (0.37, 0, -0.21), PANEL_DARK, self.stats_panel)
        _button(self.file_menu, "Save", (0.0, 0, -0.025), SMALL_BUTTON_TEXT_SCALE, self._save_from_menu)
        _button(self.file_menu, "Load", (0.0, 0, -0.080), SMALL_BUTTON_TEXT_SCALE, self._load_from_menu)
        _button(self.file_menu, "Quit", (0.0, 0, -0.135), SMALL_BUTTON_TEXT_SCALE, self._quit_from_menu)
        self.file_menu.hide()
        self.settings_menu_open = False
        self.settings_menu = _panel((-0.15, 0.15, -0.165, 0.03), (0.28, 0, -0.165), PANEL_DARK, self.stats_panel)
        _text(self.settings_menu, "Settings", (0.0, 0.015), SMALL_BUTTON_TEXT_SCALE, TextNode.ACenter, GOLD)
        self.settings_compact_button = _button(
            self.settings_menu,
            "",
            (0.0, 0, -0.058),
            SMALL_BUTTON_TEXT_SCALE,
            self.toggle_compact_tabs,
            frame_size=(-0.145, 0.145, -0.024, 0.024),
        )
        _button(self.settings_menu, "Close", (0.0, 0, -0.128), SMALL_BUTTON_TEXT_SCALE, self._close_settings_menu)
        self.settings_menu.hide()
        self._sync_settings_compact_button()

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

        self.minimap = _panel((-0.18, 0.18, -0.18, 0.18), (1.57, 0, 0.75), PANEL_LIGHT)
        _text(self.minimap, "N", (0.0, 0.135), 0.025, TextNode.ACenter, PANEL_DARK)
        _frame((-0.016, 0.016, -0.016, 0.016), (0.0, 0, 0.0), (0.88, 0.26, 0.16, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (-0.08, 0, -0.04), (0.14, 0.32, 0.76, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (0.10, 0, 0.06), (0.10, 0.44, 0.14, 1), self.minimap)
        _frame((-0.012, 0.012, -0.012, 0.012), (0.12, 0, -0.08), (0.68, 0.44, 0.20, 1), self.minimap)

        self.active_tab = ""
        self.tabs_collapsed = False
        self.tab_buttons: dict[str, DirectButton] = {}
        self.tab_frames: dict[str, DirectFrame] = {}
        self.inventory_slots: list[_InventorySlot] = []
        self.equipment_slots: dict[str, _EquipmentSlot] = {}
        self.combat_style_buttons: dict[str, DirectButton] = {}
        self.skill_rows: dict[str, _SkillRow] = {}
        self.skill_buttons: dict[str, DirectButton] = {}
        self.selected_skill_id = ""
        self._last_skills: Any | None = None
        self._build_side_tabs()
        self.select_tab(INVENTORY_TAB)

        self.bank_panel = _panel((-0.94, 0.94, -0.70, 0.62), (0.0, 0, 0.02), PANEL)
        _text(self.bank_panel, "Bank", (0.0, 0.54), BANK_TITLE_TEXT_SCALE, TextNode.ACenter, GOLD)
        _button(self.bank_panel, "Close", (0.73, 0, 0.52), 0.045, self.on_bank_close)
        _button(self.bank_panel, "Deposit all", (-0.70, 0, 0.52), 0.040, self.on_deposit_all)
        _text(self.bank_panel, "Banked Items", (-0.82, 0.43), BANK_HEADER_TEXT_SCALE, TextNode.ALeft, GOLD)
        _text(self.bank_panel, "Inventory", (0.10, 0.43), BANK_HEADER_TEXT_SCALE, TextNode.ALeft, GOLD)
        self.empty_bank_label = _text(self.bank_panel, "Bank is empty", (-0.36, 0.18), 0.038, TextNode.ACenter, MUTED_TEXT)
        self.empty_bank_inventory_label = _text(self.bank_panel, "Inventory is empty", (0.46, 0.18), 0.038, TextNode.ACenter, MUTED_TEXT)
        self.bank_rows: dict[str, _BankRow] = {}
        self.bank_inventory_rows: dict[str, _BankRow] = {}
        self.bank_panel.hide()

        self.shop_panel = _panel((-0.76, 0.76, -0.56, 0.50), (0.0, 0, 0.04), PANEL)
        _text(self.shop_panel, "General Store", (0.0, 0.43), 0.046, TextNode.ACenter, GOLD)
        _button(self.shop_panel, "Close", (0.58, 0, 0.42), 0.036, self.on_shop_close)
        self.shop_buy_tab = _button(self.shop_panel, "Buy", (-0.58, 0, 0.42), 0.033, lambda: self.select_shop_tab("buy"))
        self.shop_sell_tab = _button(self.shop_panel, "Sell", (-0.45, 0, 0.42), 0.033, lambda: self.select_shop_tab("sell"))
        self.shop_coin_label = _text(self.shop_panel, "", (0.0, 0.365), 0.028, TextNode.ACenter, GOLD, True)
        _text(self.shop_panel, "Item", (-0.52, 0.31), 0.028, TextNode.ALeft, GOLD)
        _text(self.shop_panel, "Price", (0.48, 0.31), 0.028, TextNode.ARight, GOLD)
        self.empty_shop_label = _text(self.shop_panel, "No stock available", (0.0, 0.12), 0.030, TextNode.ACenter, MUTED_TEXT, True)
        self.shop_rows: dict[str, _ShopRow] = {}
        self.shop_amount_panel = _panel((-0.28, 0.28, -0.12, 0.12), (0.0, 0, 0.02), PANEL_DARK)
        self.shop_amount_title = _text(self.shop_amount_panel, "", (0.0, 0.055), 0.030, TextNode.ACenter, GOLD, True)
        self.shop_amount_entry = DirectEntry(
            parent=self.shop_amount_panel,
            initialText="",
            width=8,
            scale=0.040,
            pos=(-0.13, 0, -0.018),
            frameColor=SLOT,
            text_fg=TEXT,
            command=self._submit_shop_amount,
        )
        _button(self.shop_amount_panel, "Ok", (0.16, 0, -0.018), 0.030, self._submit_shop_amount)
        _button(self.shop_amount_panel, "Cancel", (0.0, 0, -0.080), 0.026, self._close_shop_amount_prompt)
        self.shop_amount_panel.hide()
        self.shop_panel.hide()

        self.context_panel = _panel((-0.17, 0.17, -0.30, 0.03), (0.0, 0, 0.0), PANEL_DARK)
        self.context_panel.hide()
        self.loot_panel = _panel((-0.24, 0.24, -0.20, 0.03), (0.0, 0, 0.0), PANEL_DARK)
        self.loot_panel.hide()
        self.apply_viewport_layout(DEFAULT_VIEWPORT_ASPECT)

    def update(
        self,
        *,
        account: str,
        time_text: str,
        inventory: dict[str, int],
        bank: dict[str, int],
        skills: Any,
        equipment: dict[str, str] | None = None,
        combat_style: str = "attack",
        selected_text: str = "",
        selected_item_id: str | None = None,
        selected_item_slot: tuple[str, int] | None = None,
        shop_stock: list[dict[str, object]] | None = None,
        gather_progress: float | None = None,
        quest_objective_text: str = "",
        quest_objective_completed: bool = False,
    ) -> None:
        if shop_stock is not None:
            self.shop_stock = list(shop_stock)
        self._last_inventory = dict(inventory)
        self._last_bank = dict(bank)
        self._last_skills = skills
        self.stats.setText(f"Account: {account}")
        if selected_item_slot is None and selected_item_id is not None:
            selected_item_slot = (selected_item_id, 0)
        self._sync_inventory_slots(inventory, selected_item_slot)
        self._sync_equipment_slots(equipment or {})
        self._sync_combat_style(combat_style)
        self._sync_skill_labels(skills)
        self._sync_skill_detail()

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
        if self.file_menu_open:
            self._close_file_menu()
            return
        self._close_settings_menu()
        self.file_menu_open = True
        self.file_menu.show()

    def toggle_settings_menu(self) -> None:
        if self.settings_menu_open:
            self._close_settings_menu()
            return
        self._close_file_menu()
        self.settings_menu_open = True
        self.settings_menu.show()
        self._sync_settings_compact_button()

    def toggle_compact_tabs(self) -> None:
        self.select_tab(self.active_tab)
        self._sync_settings_compact_button()

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
        self.hide_context_menu()
        self.hide_loot_window()
        self._close_quantity_prompt()
        self.bank_is_open = True
        self.bank_panel.show()

    def close_bank(self) -> None:
        self.bank_is_open = False
        self.hide_context_menu()
        self.hide_loot_window()
        self._close_quantity_prompt()
        self.bank_panel.hide()

    def open_shop(self) -> None:
        self.quantity_mode = "1"
        self.shop_tab = "buy"
        self.shop_selected_row_id = ""
        self.hide_context_menu()
        self.hide_loot_window()
        self._close_quantity_prompt()
        self._sync_shop_tabs()
        self.shop_is_open = True
        self.shop_panel.show()

    def close_shop(self) -> None:
        self.shop_is_open = False
        self.hide_context_menu()
        self.hide_loot_window()
        self._close_quantity_prompt()
        self.shop_panel.hide()

    def select_shop_tab(self, tab_id: str) -> None:
        if tab_id not in {"buy", "sell"}:
            return
        self.shop_tab = tab_id
        self.shop_selected_row_id = ""
        self.hide_context_menu()
        self.hide_loot_window()
        self._close_quantity_prompt()
        self._sync_shop_tabs()
        self._sync_shop_rows(getattr(self, "_last_inventory", {}), self.shop_stock)

    def show_context_menu(
        self,
        actions: list[tuple[str, str]],
        command: Callable[[str], None],
        pos: tuple[float, float, float] = (0.0, 0, 0.20),
    ) -> None:
        self.hide_context_menu()
        self.hide_loot_window()
        if not actions:
            return
        self.context_panel.setPos(*_clamp_floating_panel_pos(pos, self.viewport_aspect, self.context_panel))
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

    def show_loot_window(
        self,
        entries: list[tuple[str, str]],
        command: Callable[[str], None],
        tile: tuple[int, int],
        pos: tuple[float, float, float] = (0.0, 0, 0.20),
    ) -> None:
        self.hide_context_menu()
        self.hide_loot_window()
        if not entries:
            return
        visible_entries = entries[:9]
        bottom = -0.045 - len(visible_entries) * 0.055
        frame_size = (-0.24, 0.24, bottom, 0.035)
        _set_panel_frame_size(self.loot_panel, frame_size)
        self.loot_panel.setPos(*_clamp_floating_panel_pos(pos, self.viewport_aspect, self.loot_panel))
        self.loot_tile = tile
        self.loot_command = command
        self.loot_panel.show()
        for index, (object_id, label) in enumerate(visible_entries):
            button = _button(
                self.loot_panel,
                label,
                (0.0, 0, -0.035 - index * 0.055),
                0.023,
                lambda object_id=object_id: self._choose_loot_item(object_id),
                frame_size=(-0.21, 0.21, -0.024, 0.024),
            )
            self.loot_buttons.append(button)

    def hide_loot_window(self) -> None:
        for button in self.loot_buttons:
            button.destroy()
        self.loot_buttons.clear()
        self.loot_tile = None
        self.loot_command = None
        if hasattr(self, "loot_panel"):
            self.loot_panel.hide()

    def has_open_loot_window(self) -> bool:
        return not _widget_hidden(getattr(self, "loot_panel", None))

    def close_transients(self) -> bool:
        if not _widget_hidden(self.shop_amount_panel):
            self._close_quantity_prompt()
            return True
        if not _widget_hidden(self.loot_panel):
            self.hide_loot_window()
            return True
        if not _widget_hidden(self.context_panel):
            self.hide_context_menu()
            return True
        if self.settings_menu_open:
            self._close_settings_menu()
            return True
        if self.file_menu_open:
            self._close_file_menu()
            return True
        return False

    def close_transient_if_outside(self, mouse_pos: object | None) -> bool:
        point = _mouse_point(mouse_pos)
        if point is None:
            return False
        x, z = point
        for region in (_region_for(self.file_button), _region_for(self.settings_button)):
            if region is not None and _point_in_region(x, z, region):
                return False
        if not _widget_hidden(self.shop_amount_panel):
            region = _region_for(self.shop_amount_panel)
            if not _point_in_region(x, z, region):
                self._close_quantity_prompt()
                return True
        if not _widget_hidden(self.loot_panel):
            region = _region_for(self.loot_panel)
            if not _point_in_region(x, z, region):
                self.hide_loot_window()
                return True
        if not _widget_hidden(self.context_panel):
            region = _region_for(self.context_panel)
            if not _point_in_region(x, z, region):
                self.hide_context_menu()
                return True
        if self.settings_menu_open:
            region = _region_for(self.settings_menu)
            if not _point_in_region(x, z, region):
                self._close_settings_menu()
                return True
        if self.file_menu_open:
            region = _region_for(self.file_menu)
            if not _point_in_region(x, z, region):
                self._close_file_menu()
                return True
        return False

    def pointer_over_blocking_ui(self, mouse_pos: object | None) -> bool:
        point = _mouse_point(mouse_pos)
        if point is None:
            return False
        x, z = point
        regions = [
            _region_for(self.stats_panel),
            _region_for(self.feedback_panel),
            _region_for(self.quest_panel),
            _region_for(self.chat_panel),
            _region_for(self.minimap),
            _region_for(self.tab_box) if not _widget_hidden(self.tab_box) else None,
            _region_for(self.skill_detail_panel) if not _widget_hidden(getattr(self, "skill_detail_panel", None)) else None,
            _region_for(self.bank_panel) if self.bank_is_open else None,
            _region_for(self.shop_panel) if self.shop_is_open else None,
            _region_for(self.context_panel) if not _widget_hidden(self.context_panel) else None,
            _region_for(self.loot_panel) if not _widget_hidden(self.loot_panel) else None,
            _region_for(self.shop_amount_panel) if not _widget_hidden(self.shop_amount_panel) else None,
            _region_for(self.settings_menu) if self.settings_menu_open else None,
            _region_for(self.file_menu) if self.file_menu_open else None,
        ]
        return any(_point_in_region(x, z, region) for region in regions if region is not None)

    def apply_viewport_layout(self, aspect: float) -> None:
        self.viewport_aspect = max(1.0, float(aspect))
        _set_widget_pos(self.stats_panel, _anchor_pos(self.stats_panel, self.viewport_aspect, "left", "top"))
        _set_widget_pos(self.feedback_panel, _anchor_pos(self.feedback_panel, self.viewport_aspect, "center", "top"))
        feedback_region = _region_for(self.feedback_panel)
        quest_frame = _widget_option(self.quest_panel, "frameSize")
        if feedback_region is not None and quest_frame is not None:
            try:
                quest_top = float(quest_frame[3])  # type: ignore[index]
            except (TypeError, ValueError, IndexError):
                quest_top = 0.04
            _set_widget_pos(self.quest_panel, (0.0, 0, feedback_region[2] - quest_top))
        _set_widget_pos(self.chat_panel, _anchor_pos(self.chat_panel, self.viewport_aspect, "left", "bottom"))
        _set_widget_pos(self.minimap, _anchor_pos(self.minimap, self.viewport_aspect, "right", "top"))
        _set_widget_pos(self.tab_box, _anchor_pos(self.tab_box, self.viewport_aspect, "right", "bottom"))

    def _choose_context_action(self, action_id: str, command: Callable[[str], None]) -> None:
        self.hide_context_menu()
        command(action_id)

    def _choose_loot_item(self, object_id: str) -> None:
        command = self.loot_command
        if command is not None:
            command(object_id)

    def _close_file_menu(self) -> None:
        self.file_menu_open = False
        self.file_menu.hide()

    def _close_settings_menu(self) -> None:
        self.settings_menu_open = False
        self.settings_menu.hide()

    def _sync_settings_compact_button(self) -> None:
        if hasattr(self, "settings_compact_button"):
            self.settings_compact_button["text"] = f"Compact HUD: {'On' if getattr(self, 'tabs_collapsed', False) else 'Off'}"

    def select_tab(self, tab_id: str) -> None:
        if tab_id not in self.tab_frames:
            return
        if tab_id == self.active_tab and not self.tabs_collapsed:
            self._set_tabs_collapsed(True)
            return
        self.set_ui_hover_text("")
        self.active_tab = tab_id
        self._set_tabs_collapsed(False)
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

    def _set_tabs_collapsed(self, collapsed: bool) -> None:
        self.tabs_collapsed = collapsed
        _set_panel_frame_size(self.tab_box, TAB_BOX_COLLAPSED_FRAME_SIZE if collapsed else TAB_BOX_FRAME_SIZE)
        if collapsed:
            self.tab_box.show()
            for frame in self.tab_frames.values():
                frame.hide()
        else:
            self.tab_box.show()
        self.apply_viewport_layout(self.viewport_aspect)
        self._sync_settings_compact_button()

    def _build_side_tabs(self) -> None:
        tab_labels = {
            INVENTORY_TAB: "Inv",
            CLOTHES_TAB: "Gear",
            SKILLS_TAB: "Skill",
        }
        tab_positions = {
            INVENTORY_TAB: -0.145,
            SKILLS_TAB: 0.0,
            CLOTHES_TAB: 0.145,
        }
        self.tab_box = _panel(TAB_BOX_FRAME_SIZE, TAB_BOX_POS, PANEL_DARK)
        for tab_id in TAB_ORDER:
            self.tab_buttons[tab_id] = _button(
                self.tab_box,
                tab_labels[tab_id],
                (tab_positions[tab_id], 0, 0.005),
                SIDE_TAB_TEXT_SCALE,
                lambda tab_id=tab_id: self.select_tab(tab_id),
                frame_size=TAB_BUTTON_FRAME_SIZE,
            )

        for tab_id in TAB_ORDER:
            self.tab_frames[tab_id] = _frame((-0.225, 0.225, -0.925, -0.055), (0.0, 0, 0.0), UI.TRANSPARENT, self.tab_box)

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
            button.bind(DGG.B3PRESS, lambda _event=None, index=index: self._show_inventory_context(index))
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
            equipment_slot = _EquipmentSlot(button=button, icon=_SlotIcon.create(button), empty_label=label)
            equipment_slot.clear()
            self.equipment_slots[slot_id] = equipment_slot
        self._build_combat_style_buttons(parent)

    def _build_combat_style_buttons(self, parent: DirectFrame) -> None:
        for style, label, x, z in (
            ("attack", "Attack", -0.135, -0.805),
            ("strength", "Strength", 0.0, -0.805),
            ("defence", "Defence", 0.135, -0.805),
            ("ranged", "Ranged", -0.070, -0.875),
            ("magic", "Magic", 0.070, -0.875),
        ):
            self.combat_style_buttons[style] = _button(
                parent,
                label,
                (x, 0, z),
                0.020,
                lambda style=style: self.on_combat_style(style),
            )

    def _build_skills_tab(self, parent: DirectFrame) -> None:
        for index, skill_id in enumerate(self.skill_ids):
            z = -0.075 - index * SKILL_ROW_SPACING
            button = _skill_button(parent, skill_id, (-0.178, 0, z - 0.010), lambda skill_id=skill_id: self.select_skill_detail(skill_id))
            self.skill_buttons[skill_id] = button
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
        self.skill_detail_panel = _panel((-0.58, 0.58, -0.36, 0.34), (-0.58, 0, 0.18), PANEL_DARK)
        self.skill_detail_title = _text(self.skill_detail_panel, "", (0.0, 0.270), 0.040, TextNode.ACenter, GOLD, True)
        self.skill_detail_lines = [
            _text(self.skill_detail_panel, "", (-0.50, 0.205 - index * 0.043), 0.024, TextNode.ALeft, TEXT, True)
            for index in range(12)
        ]
        _button(self.skill_detail_panel, "Close", (0.46, 0, 0.275), 0.028, self.close_skill_detail)
        self.skill_detail_panel.hide()

    def _select_inventory_slot(self, index: int) -> None:
        if index < 0 or index >= len(self.inventory_slots):
            return
        item_id = self.inventory_slots[index].item_id
        if item_id is not None:
            self.on_select_item(item_id, self.inventory_slots[index].occurrence_index)

    def _show_inventory_context(self, index: int) -> None:
        if index < 0 or index >= len(self.inventory_slots):
            return
        slot = self.inventory_slots[index]
        if slot.item_id is None:
            return
        item_id = slot.item_id
        name = _item_name(self.items_data, item_id)
        self.show_context_menu(
            [("examine", f"Examine {name}"), ("drop", f"Drop {name}"), ("cancel", "Cancel")],
            lambda action_id, item_id=item_id: self._choose_inventory_context(item_id, action_id),
            pos=(-0.34, 0, 0.12),
        )

    def _choose_inventory_context(self, item_id: str, action_id: str) -> None:
        if action_id == "examine":
            self.on_examine_item(item_id)
        elif action_id == "drop":
            self.on_drop_item(item_id)

    def _sync_inventory_slots(self, inventory: dict[str, int], selected_item_slot: tuple[str, int] | None) -> None:
        visible_slots = _inventory_slot_views(self.items_data, inventory)[:INVENTORY_SLOT_COUNT]
        for index, slot in enumerate(self.inventory_slots):
            if index < len(visible_slots):
                view = visible_slots[index]
                slot.set_item(
                    self.items_data,
                    view.item_id,
                    view.quantity,
                    (view.item_id, view.occurrence_index) == selected_item_slot,
                    occurrence_index=view.occurrence_index,
                    show_quantity=view.show_quantity,
                )
            else:
                slot.clear()

    def _sync_equipment_slots(self, equipment: dict[str, str]) -> None:
        for slot_id, slot in self.equipment_slots.items():
            item_id = equipment.get(slot_id)
            if item_id:
                slot.set_item(self.items_data, item_id)
            else:
                slot.clear()

    def _sync_combat_style(self, combat_style: str) -> None:
        active_style = combat_style if combat_style in self.combat_style_buttons else "attack"
        for style, button in self.combat_style_buttons.items():
            active = style == active_style
            button["frameColor"] = (
                SLOT_HILITE if active else BUTTON,
                BUTTON_HOVER,
                BUTTON_HOVER,
                SLOT_HILITE if active else BUTTON,
            )
            button["text_fg"] = TEXT if active else MUTED_TEXT

    def _sync_skill_labels(self, skills: Any) -> None:
        for skill_id, row in self.skill_rows.items():
            row.set_skill(_skill_label(self.skills_data, skill_id), skills.get(skill_id))
        for skill_id, button in self.skill_buttons.items():
            active = skill_id == self.selected_skill_id
            button["frameColor"] = (
                SLOT_HILITE if active else SLOT,
                BUTTON_HOVER,
                BUTTON_HOVER,
                SLOT_HILITE if active else SLOT,
            )

    def select_skill_detail(self, skill_id: str) -> None:
        if skill_id not in self.skill_ids:
            return
        self.selected_skill_id = skill_id
        self.skill_detail_panel.show()
        for candidate_id, button in self.skill_buttons.items():
            active = candidate_id == skill_id
            button["frameColor"] = (
                SLOT_HILITE if active else SLOT,
                BUTTON_HOVER,
                BUTTON_HOVER,
                SLOT_HILITE if active else SLOT,
            )
        self._sync_skill_detail()

    def close_skill_detail(self) -> None:
        self.selected_skill_id = ""
        self.skill_detail_panel.hide()
        for button in self.skill_buttons.values():
            button["frameColor"] = (SLOT, BUTTON_HOVER, BUTTON_HOVER, SLOT)

    def _sync_skill_detail(self) -> None:
        if not self.selected_skill_id or _widget_hidden(getattr(self, "skill_detail_panel", None)):
            return
        skill_id = self.selected_skill_id
        label = _skill_label(self.skills_data, skill_id)
        state = self._last_skills.get(skill_id) if self._last_skills is not None else None
        level_text = _skill_detail_text(state) if state is not None else ""
        self.skill_detail_title.setText(f"{_skill_name_text(label)} {level_text}".strip())
        lines = _skill_unlock_lines(
            skill_id,
            self.items_data,
            self.world_data,
            self.recipes_data,
            self._last_skills,
        )
        if not lines:
            lines = ["No unlocks listed yet."]
        for index, line in enumerate(self.skill_detail_lines):
            line.setText(lines[index] if index < len(lines) else "")

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
        bank_item_ids = _bank_item_ids(self.items_data, {}, bank)
        inventory_item_ids = _inventory_item_ids(self.items_data, inventory)

        for item_id in list(self.bank_rows):
            if item_id not in bank_item_ids:
                self.bank_rows.pop(item_id).destroy()
        for item_id in list(self.bank_inventory_rows):
            if item_id not in inventory_item_ids:
                self.bank_inventory_rows.pop(item_id).destroy()

        if bank_item_ids:
            self.empty_bank_label.hide()
        else:
            self.empty_bank_label.show()
        if inventory_item_ids:
            self.empty_bank_inventory_label.hide()
        else:
            self.empty_bank_inventory_label.show()

        self._sync_bank_row_group(
            self.bank_rows,
            bank_item_ids,
            bank,
            x=-0.82,
            top_y=0.35,
            action="withdraw",
        )
        self._sync_bank_row_group(
            self.bank_inventory_rows,
            inventory_item_ids,
            inventory,
            x=0.10,
            top_y=0.35,
            action="deposit",
        )

    def _sync_bank_row_group(
        self,
        rows: dict[str, "_BankRow"],
        item_ids: list[str],
        quantities: dict[str, int],
        *,
        x: float,
        top_y: float,
        action: str,
    ) -> None:
        for index, item_id in enumerate(item_ids[:9]):
            y = top_y - index * BANK_ROW_SPACING
            row = rows.get(item_id)
            if row is None:
                button = _shop_icon_button(
                    self.bank_panel,
                    (x, 0, y + 0.006),
                    lambda item_id=item_id, action=action: self._bank_left_click(item_id, action),
                    size=0.040,
                )
                button.bind(
                    DGG.B3PRESS,
                    lambda _event=None, item_id=item_id, action=action: self._show_bank_quantity(item_id, action),
                )
                row = _BankRow(
                    item_button=button,
                    icon=_SlotIcon.create(button),
                    item_label=_text(self.bank_panel, _item_name(self.items_data, item_id), (x + 0.07, y + 0.012), BANK_ROW_TEXT_SCALE, TextNode.ALeft, TEXT, True),
                    quantity_label=_text(self.bank_panel, "", (x + 0.07, y - 0.022), 0.023, TextNode.ALeft, GOLD, True),
                )
                rows[item_id] = row
            row.icon.set_item(self.items_data, item_id)
            row.set_pos(x, y)
            row.quantity_label.setText(f"Qty {quantities.get(item_id, 0)}")

    def _bank_left_click(self, item_id: str, action: str) -> None:
        self.quantity_mode = "1"
        if action == "withdraw":
            self.on_withdraw_item(item_id)
        else:
            self.on_deposit_item(item_id)

    def _show_bank_quantity(self, item_id: str, action: str) -> None:
        available = 0
        if action == "withdraw":
            row_source = getattr(self, "_last_bank", {})
            available = int(row_source.get(item_id, 0))
        else:
            available = int(getattr(self, "_last_inventory", {}).get(item_id, 0))
        if available <= 0:
            return
        self.show_quantity_menu(
            action,
            _item_name(self.items_data, item_id),
            available,
            lambda quantity, item_id=item_id, action=action: self._choose_bank_quantity(item_id, action, quantity),
        )

    def _choose_bank_quantity(self, item_id: str, action: str, quantity: int) -> None:
        self.quantity_mode = str(max(1, quantity))
        if action == "withdraw":
            self.on_withdraw_item(item_id)
        else:
            self.on_deposit_item(item_id)

    def _sync_shop_rows(self, inventory: dict[str, int], shop_stock: list[dict[str, object]]) -> None:
        self.shop_coin_label.setText(f"Coins: {inventory.get(COINS_ITEM_ID, 0)}")
        self._sync_shop_tabs()
        stock_prices = _stock_prices(shop_stock)
        buy_item_ids = sorted(stock_prices, key=lambda item_id: (_category_sort_key(self.items_data, item_id), item_id))
        sell_item_ids = [
            item_id
            for item_id in _sellable_item_ids(self.items_data, inventory)
            if item_id not in stock_prices and item_id != COINS_ITEM_ID
        ]
        if self.shop_tab == "sell":
            visible_rows = [(f"sell:{item_id}", item_id, "sell") for item_id in sell_item_ids]
        else:
            visible_rows = [(item_id, item_id, "buy") for item_id in buy_item_ids]
        visible_row_ids = {row_id for row_id, _item_id, _mode in visible_rows}

        for item_id in list(self.shop_rows):
            if item_id not in visible_row_ids:
                self.shop_rows.pop(item_id).destroy()

        if visible_rows:
            self.empty_shop_label.hide()
        else:
            self.empty_shop_label.show()
            self.empty_shop_label.setText("Nothing to sell" if self.shop_tab == "sell" else "No stock available")

        for index, (row_id, item_id, mode) in enumerate(visible_rows):
            y = 0.235 - index * 0.074
            row = self.shop_rows.get(row_id)
            if row is None:
                item_button = _shop_icon_button(
                    self.shop_panel,
                    (-0.60, 0, y + 0.006),
                    lambda row_id=row_id, item_id=item_id, mode=mode: self._select_shop_row(row_id, item_id, mode),
                    size=0.046,
                )
                item_button.bind(
                    DGG.B3PRESS,
                    lambda _event=None, row_id=row_id, item_id=item_id, mode=mode: self._show_shop_context(row_id, item_id, mode),
                )
                row = _ShopRow(
                    row_id=row_id,
                    mode=mode,
                    item_button=item_button,
                    icon=_SlotIcon.create(item_button),
                    item_label=_text(self.shop_panel, _item_name(self.items_data, item_id), (-0.52, y), 0.030, TextNode.ALeft, TEXT, True),
                    quantity_label=_text(self.shop_panel, "", (-0.645, y - 0.030), 0.020, TextNode.ACenter, GOLD, True),
                    price_label=_text(self.shop_panel, "", (0.48, y), 0.030, TextNode.ARight, TEXT, True),
                )
                self.shop_rows[row_id] = row
            row.icon.set_item(self.items_data, item_id)
            row.mode = mode
            row.set_pos(y)
            row.set_selected(row_id == self.shop_selected_row_id)
            row.quantity_label.setText(str(inventory.get(item_id, 0)))
            if mode == "buy":
                row.quantity_label.hide()
            else:
                row.quantity_label.show()
            row.price_label.setText(str(stock_prices[item_id] if mode == "buy" else _sell_price(self.items_data, item_id)))

    def _sync_shop_tabs(self) -> None:
        for tab_id, button in (("buy", self.shop_buy_tab), ("sell", self.shop_sell_tab)):
            active = self.shop_tab == tab_id
            button["frameColor"] = (
                SLOT_HILITE if active else BUTTON,
                BUTTON_HOVER,
                BUTTON_HOVER,
                SLOT_HILITE if active else BUTTON,
            )
            button["text_fg"] = TEXT if active else MUTED_TEXT

    def _select_shop_row(self, row_id: str, item_id: str, mode: str) -> None:
        self.shop_selected_row_id = row_id
        verb = "Right-click to buy" if mode == "buy" else "Right-click to sell"
        self.set_ui_hover_text(f"{verb} {_item_name(self.items_data, item_id)}")
        for candidate_id, row in self.shop_rows.items():
            row.set_selected(candidate_id == row_id)

    def _show_shop_context(self, row_id: str, item_id: str, mode: str) -> None:
        self._select_shop_row(row_id, item_id, mode)
        available = int(getattr(self, "_last_inventory", {}).get(item_id, 0))
        if mode == "buy":
            available = 10_000
        if available <= 0:
            return
        self.show_quantity_menu(
            mode,
            _item_name(self.items_data, item_id),
            available,
            lambda quantity, mode=mode, item_id=item_id: self._choose_shop_quantity(mode, item_id, quantity),
        )

    def _choose_shop_quantity(self, mode: str, item_id: str, quantity: int) -> None:
        self.quantity_mode = str(max(1, quantity))
        if mode == "buy":
            self.on_buy_item(item_id)
        else:
            self.on_sell_item(item_id)

    def show_quantity_menu(
        self,
        action: str,
        label: str,
        max_quantity: int,
        command: Callable[[int], None],
    ) -> None:
        max_quantity = max(1, int(max_quantity))
        verb = _quantity_verb(action)
        actions = [
            ("1", f"{verb} 1 {label}"),
            ("5", f"{verb} 5 {label}"),
            ("10", f"{verb} 10 {label}"),
            ("x", f"{verb} X {label}"),
            ("all", f"{verb} All {label}"),
        ]
        self.show_context_menu(
            actions,
            lambda action_id, action=action, label=label, max_quantity=max_quantity, command=command: self._choose_quantity_action(
                action_id,
                action,
                label,
                max_quantity,
                command,
            ),
            pos=(-0.48, 0, 0.24),
        )

    def _choose_quantity_action(
        self,
        action_id: str,
        action: str,
        label: str,
        max_quantity: int,
        command: Callable[[int], None],
    ) -> None:
        if action_id == "x":
            self._open_quantity_prompt(action, label, max_quantity, command)
            return
        quantity = max_quantity if action_id == "all" else min(max_quantity, int(action_id))
        command(quantity)

    def _open_quantity_prompt(
        self,
        action: str,
        label: str,
        max_quantity: int,
        command: Callable[[int], None],
    ) -> None:
        self.quantity_context = (action, label, max_quantity, command)
        verb = _quantity_verb(action)
        self.shop_amount_title.setText(f"{verb} how many?")
        self.shop_amount_entry["text"] = ""
        self.shop_amount_panel.show()

    def _close_quantity_prompt(self) -> None:
        self.quantity_context = None
        self.shop_amount_context = None
        if hasattr(self, "shop_amount_panel"):
            self.shop_amount_panel.hide()

    def _close_shop_amount_prompt(self) -> None:
        self._close_quantity_prompt()

    def _submit_shop_amount(self, value: str | None = None) -> None:
        if self.quantity_context is None:
            return
        raw_value = value
        if raw_value is None:
            get_value = getattr(self.shop_amount_entry, "get", None)
            raw_value = str(get_value()) if callable(get_value) else str(getattr(self.shop_amount_entry, "text", ""))
        try:
            quantity = int(str(raw_value).strip())
        except ValueError:
            quantity = 0
        if quantity <= 0:
            self.set_feedback("Enter a positive quantity")
            self._close_quantity_prompt()
            return
        _action, _label, max_quantity, command = self.quantity_context
        quantity = min(max_quantity, quantity)
        self._close_quantity_prompt()
        command(quantity)

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
class _InventorySlotView:
    item_id: str
    quantity: int
    show_quantity: bool
    occurrence_index: int = 0


@dataclass
class _InventorySlot:
    button: DirectButton
    icon: "_SlotIcon"
    on_hover: Callable[[str], None]
    item_id: str | None = None
    occurrence_index: int = 0
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
        *,
        occurrence_index: int = 0,
        show_quantity: bool = True,
    ) -> None:
        if quantity <= 0:
            self.clear()
            return
        self.item_id = item_id
        self.occurrence_index = occurrence_index
        self.hover_text = _inventory_hover_text(items_data, item_id, quantity)
        base_color = SLOT_HILITE if selected else SLOT
        hover_color = SLOT_HILITE if selected else BUTTON_HOVER
        self.button["text"] = _format_quantity(quantity) if show_quantity else ""
        self.button["text_fg"] = TEXT
        self.button["frameColor"] = (base_color, hover_color, hover_color, base_color)
        self.icon.set_item(items_data, item_id)
        if self.is_hovered:
            self.on_hover(self.hover_text)

    def clear(self) -> None:
        self.item_id = None
        self.occurrence_index = 0
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
                for _ in range(12)
            ],
            label=_icon_label(parent),
        )
        icon.clear()
        return icon

    def set_item(self, items_data: dict[str, dict[str, object]], item_id: str) -> None:
        specs = _item_icon_specs(items_data, item_id)
        label = _item_icon_label(items_data, item_id)
        self.label.setText(label)
        if label:
            self.label.show()
        else:
            self.label.hide()
        for index, part in enumerate(self.parts):
            if index < len(specs):
                spec = specs[index]
                frame_size, pos, color = spec[:3]
                roll = float(spec[3]) if len(spec) > 3 else 0.0
                part["frameSize"] = frame_size
                part["pos"] = pos
                part["frameColor"] = color
                _set_widget_roll(part, roll)
                part.show()
            else:
                _set_widget_roll(part, 0.0)
                part.hide()

    def clear(self) -> None:
        for part in self.parts:
            _set_widget_roll(part, 0.0)
            part.hide()
        self.label.setText("")
        self.label.hide()

    def destroy(self) -> None:
        for part in self.parts:
            part.destroy()
        self.label.destroy()


@dataclass
class _EquipmentSlot:
    button: DirectButton
    icon: "_SlotIcon"
    empty_label: str

    def set_item(self, items_data: dict[str, dict[str, object]], item_id: str) -> None:
        self.button["text"] = ""
        self.button["text_fg"] = TEXT
        self.button["frameColor"] = (SLOT_HILITE, BUTTON_HOVER, BUTTON_HOVER, SLOT_HILITE)
        self.icon.set_item(items_data, item_id)

    def clear(self) -> None:
        self.button["text"] = self.empty_label
        self.button["text_fg"] = MUTED_TEXT
        self.button["frameColor"] = (SLOT, SLOT, SLOT, SLOT)
        self.icon.clear()


@dataclass
class _SkillRow:
    name_label: OnscreenText
    detail_label: OnscreenText

    def set_skill(self, label: str, state: Any) -> None:
        self.name_label.setText(_skill_name_text(label))
        self.detail_label.setText(_skill_detail_text(state))


@dataclass
class _BankRow:
    item_button: DirectButton
    icon: "_SlotIcon"
    item_label: OnscreenText
    quantity_label: OnscreenText

    def set_pos(self, x: float, y: float) -> None:
        self.item_button.setPos(x, 0, y + 0.006)
        self.item_label.setPos(x + 0.07, y + 0.012)
        self.quantity_label.setPos(x + 0.07, y - 0.022)

    def destroy(self) -> None:
        self.icon.destroy()
        self.item_button.destroy()
        self.item_label.destroy()
        self.quantity_label.destroy()


@dataclass
class _ShopRow:
    row_id: str
    mode: str
    item_button: DirectButton
    icon: "_SlotIcon"
    item_label: OnscreenText
    quantity_label: OnscreenText
    price_label: OnscreenText

    def set_pos(self, y: float) -> None:
        self.item_button.setPos(-0.60, 0, y + 0.006)
        self.item_label.setPos(-0.52, y)
        self.quantity_label.setPos(-0.645, y - 0.030)
        self.price_label.setPos(0.48, y)

    def set_selected(self, selected: bool) -> None:
        base = SLOT_HILITE if selected else SLOT
        hover = SLOT_HILITE if selected else BUTTON_HOVER
        self.item_button["frameColor"] = (base, hover, hover, base)

    def destroy(self) -> None:
        self.icon.destroy()
        self.item_button.destroy()
        self.item_label.destroy()
        self.quantity_label.destroy()
        self.price_label.destroy()


def _mouse_point(mouse_pos: object | None) -> tuple[float, float] | None:
    if mouse_pos is None:
        return None
    try:
        if len(mouse_pos) >= 3:  # type: ignore[arg-type]
            return float(mouse_pos[0]), float(mouse_pos[2])  # type: ignore[index]
        return float(mouse_pos[0]), float(mouse_pos[1])  # type: ignore[index]
    except (TypeError, ValueError, IndexError):
        return None


def _point_in_region(x: float, z: float, region: tuple[float, float, float, float] | None) -> bool:
    if region is None:
        return False
    left, right, bottom, top = region
    return left <= x <= right and bottom <= z <= top


def _region_for(widget: object) -> tuple[float, float, float, float] | None:
    frame_size = _widget_option(widget, "frameSize")
    if frame_size is None:
        return None
    try:
        left, right, bottom, top = [float(value) for value in frame_size]
    except (TypeError, ValueError):
        return None
    x, z = _absolute_widget_pos(widget)
    return left + x, right + x, bottom + z, top + z


def _absolute_widget_pos(widget: object) -> tuple[float, float]:
    x, z = _widget_pos(widget)
    parent = _widget_option(widget, "parent")
    while parent is not None:
        parent_x, parent_z = _widget_pos(parent)
        x += parent_x
        z += parent_z
        parent = _widget_option(parent, "parent")
    return x, z


def _widget_pos(widget: object) -> tuple[float, float]:
    pos = getattr(widget, "pos", None)
    if pos is None:
        get_pos = getattr(widget, "getPos", None)
        if callable(get_pos):
            pos = get_pos()
    if pos is None:
        pos = _widget_option(widget, "pos", (0.0, 0.0, 0.0))
    try:
        if len(pos) >= 3:  # type: ignore[arg-type]
            return float(pos[0]), float(pos[2])  # type: ignore[index]
        return float(pos[0]), float(pos[1])  # type: ignore[index]
    except (TypeError, ValueError, IndexError):
        return 0.0, 0.0


def _widget_option(widget: object, key: str, default: object | None = None) -> object | None:
    options = getattr(widget, "options", None)
    if isinstance(options, dict) and key in options:
        return options[key]
    try:
        return widget[key]  # type: ignore[index]
    except Exception:
        return default


def _widget_hidden(widget: object) -> bool:
    if bool(getattr(widget, "hidden", False)):
        return True
    is_hidden = getattr(widget, "isHidden", None)
    return bool(is_hidden()) if callable(is_hidden) else False


def _set_widget_roll(widget: object, roll: float) -> None:
    set_r = getattr(widget, "setR", None)
    if callable(set_r):
        set_r(roll)
        return
    try:
        widget["roll"] = roll  # type: ignore[index]
    except Exception:
        pass


def _set_widget_pos(widget: object, pos: tuple[float, float, float]) -> None:
    set_pos = getattr(widget, "setPos", None)
    if callable(set_pos):
        set_pos(*pos)
        return
    try:
        widget["pos"] = pos  # type: ignore[index]
    except Exception:
        pass


def _anchor_pos(widget: object, aspect: float, x_anchor: str, z_anchor: str) -> tuple[float, float, float]:
    frame_size = _widget_option(widget, "frameSize")
    try:
        left, right, bottom, top = [float(value) for value in frame_size]  # type: ignore[union-attr]
    except (TypeError, ValueError):
        return (0.0, 0, 0.0)
    if x_anchor == "left":
        x = -aspect - left
    elif x_anchor == "right":
        x = aspect - right
    else:
        x = 0.0
    if z_anchor == "top":
        z = 1.0 - top
    elif z_anchor == "bottom":
        z = -1.0 - bottom
    else:
        z = 0.0
    return (x, 0, z)


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
    inner = _frame((left + border, right - border, bottom + border, top - border), (0, 0, 0), color, panel)
    panel.inner_frame = inner
    return panel


def _set_panel_frame_size(panel: DirectFrame, frame_size: tuple[float, float, float, float], border: float = 0.012) -> None:
    panel["frameSize"] = frame_size
    inner = getattr(panel, "inner_frame", None)
    if inner is None:
        return
    left, right, bottom, top = frame_size
    inner["frameSize"] = (left + border, right - border, bottom + border, top - border)


def _button(
    parent: Any,
    text: str,
    pos: tuple[float, float, float],
    scale: float,
    command: Callable[[], None],
    *,
    frame_size: tuple[float, float, float, float] | None = None,
) -> DirectButton:
    kwargs: dict[str, Any] = {
        "parent": parent,
        "text": text,
        "pos": pos,
        "scale": scale,
        "frameColor": (BUTTON, BUTTON_HOVER, BUTTON_HOVER, BUTTON),
        "text_fg": TEXT,
        "command": command,
    }
    if frame_size is not None:
        kwargs["frameSize"] = frame_size
    return DirectButton(**kwargs)


def _clamp_context_menu_pos(pos: tuple[float, float, float]) -> tuple[float, float, float]:
    return _clamp_floating_panel_pos(pos, DEFAULT_VIEWPORT_ASPECT, (-0.17, 0.17, -0.30, 0.03))


def _clamp_floating_panel_pos(
    pos: tuple[float, float, float],
    aspect: float,
    widget_or_frame: object,
) -> tuple[float, float, float]:
    x, y, z = pos
    frame_size = widget_or_frame if isinstance(widget_or_frame, tuple) else _widget_option(widget_or_frame, "frameSize")
    try:
        left, right, bottom, top = [float(value) for value in frame_size]  # type: ignore[union-attr]
    except (TypeError, ValueError):
        left, right, bottom, top = -0.17, 0.17, -0.30, 0.03
    min_x = -aspect - left
    max_x = aspect - right
    min_z = -1.0 - bottom
    max_z = 1.0 - top
    return (max(min_x, min(max_x, x)), y, max(min_z, min(max_z, z)))


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


def _skill_button(parent: Any, skill_id: str, pos: tuple[float, float, float], command: Callable[[], None]) -> DirectButton:
    button = DirectButton(
        parent=parent,
        pos=pos,
        frameSize=(-0.033, 0.033, -0.033, 0.033),
        frameColor=(SLOT, BUTTON_HOVER, BUTTON_HOVER, SLOT),
        text="",
        command=command,
    )
    _skill_icon(button, skill_id, (0.0, 0, 0.0))
    return button


def _shop_icon_button(
    parent: Any,
    pos: tuple[float, float, float],
    command: Callable[[], None],
    *,
    size: float = 0.034,
) -> DirectButton:
    return DirectButton(
        parent=parent,
        pos=pos,
        frameSize=(-size, size, -size, size),
        frameColor=(SLOT, BUTTON_HOVER, BUTTON_HOVER, SLOT),
        text="",
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


def _select_item_callback(callback: Callable[[str, int], None] | None) -> Callable[[str, int], None]:
    if callback is None:
        return lambda _item_id, _occurrence_index=0: None

    def wrapped(item_id: str, occurrence_index: int = 0) -> None:
        try:
            callback(item_id, occurrence_index)
        except TypeError:
            callback(item_id)  # type: ignore[misc, call-arg]

    return wrapped


def _skill_icon(parent: Any, skill_id: str, pos: tuple[float, float, float]) -> None:
    color = {
        "woodcutting": (0.42, 0.25, 0.10, 1.0),
        "mining": (0.52, 0.52, 0.48, 1.0),
        "fishing": (0.25, 0.48, 0.64, 1.0),
        "cooking": (0.72, 0.36, 0.18, 1.0),
        "attack": (0.62, 0.18, 0.14, 1.0),
        "strength": (0.72, 0.48, 0.18, 1.0),
        "defence": (0.26, 0.34, 0.68, 1.0),
        "ranged": (0.20, 0.50, 0.24, 1.0),
        "magic": (0.34, 0.30, 0.72, 1.0),
        "hitpoints": (0.72, 0.12, 0.18, 1.0),
        "smithing": (0.42, 0.42, 0.38, 1.0),
    }.get(skill_id, SLOT_HILITE)
    _frame((-0.026, 0.026, -0.026, 0.026), pos, SLOT, parent)
    if skill_id == "woodcutting":
        _frame((-0.004, 0.004, -0.026, 0.026), (-0.004, 0, 0.000), (0.54, 0.30, 0.12, 1.0), parent)
        _frame((-0.024, 0.010, -0.008, 0.008), (0.010, 0, 0.020), color, parent)
    elif skill_id == "mining":
        _frame((-0.004, 0.004, -0.026, 0.026), (-0.004, 0, -0.002), (0.54, 0.30, 0.12, 1.0), parent)
        _frame((-0.026, 0.026, -0.005, 0.005), (0.004, 0, 0.020), color, parent)
    elif skill_id == "fishing":
        _frame((-0.004, 0.004, -0.027, 0.027), (-0.012, 0, 0.002), (0.54, 0.30, 0.12, 1.0), parent)
        _frame((-0.020, 0.020, -0.007, 0.007), (0.008, 0, -0.008), color, parent)
        _frame((0.014, 0.026, -0.011, 0.011), (0.012, 0, -0.008), (0.18, 0.34, 0.46, 1.0), parent)
    elif skill_id == "cooking":
        _frame((-0.016, 0.016, -0.020, 0.006), (0.0, 0, -0.006), (0.20, 0.18, 0.16, 1.0), parent)
        _frame((-0.006, 0.006, -0.004, 0.022), (-0.008, 0, 0.010), color, parent)
        _frame((-0.006, 0.006, -0.004, 0.020), (0.008, 0, 0.010), GOLD, parent)
    elif skill_id in {"attack", "strength"}:
        _frame((-0.006, 0.006, -0.027, 0.027), (0.006, 0, 0.006), color, parent)
        _frame((-0.020, 0.020, -0.004, 0.004), (-0.010, 0, -0.012), (0.54, 0.30, 0.12, 1.0), parent)
    elif skill_id == "defence":
        _frame((-0.022, 0.022, -0.024, 0.020), (0.0, 0, 0.000), color, parent)
        _frame((-0.004, 0.004, -0.020, 0.018), (0.0, 0, 0.000), (0.15, 0.18, 0.28, 1.0), parent)
    elif skill_id == "ranged":
        _frame((-0.004, 0.004, -0.031, 0.031), (-0.006, 0, 0.000), (0.54, 0.30, 0.12, 1.0), parent)
        _frame((-0.026, 0.026, -0.003, 0.003), (0.006, 0, 0.016), color, parent)
        _frame((-0.018, 0.018, -0.002, 0.002), (0.010, 0, -0.017), color, parent)
    elif skill_id == "magic":
        _frame((-0.006, 0.006, -0.030, 0.030), (0.000, 0, 0.000), color, parent)
        _frame((-0.018, 0.018, -0.005, 0.005), (0.000, 0, 0.026), GOLD, parent)
        _frame((-0.012, 0.012, -0.012, 0.012), (0.000, 0, -0.022), (0.58, 0.72, 1.0, 1.0), parent)
    elif skill_id == "hitpoints":
        _frame((-0.014, 0.014, -0.018, 0.014), (-0.008, 0, 0.004), color, parent)
        _frame((-0.014, 0.014, -0.018, 0.014), (0.008, 0, 0.004), color, parent)
        _frame((-0.012, 0.012, -0.012, 0.016), (0.0, 0, -0.012), color, parent)
    elif skill_id == "smithing":
        _frame((-0.022, 0.022, -0.006, 0.006), (0.0, 0, -0.006), color, parent)
        _frame((-0.010, 0.010, -0.024, 0.018), (0.010, 0, 0.010), (0.54, 0.30, 0.12, 1.0), parent)
        _frame((-0.018, 0.018, -0.006, 0.006), (-0.004, 0, 0.024), GOLD, parent)
    else:
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
    return ""


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
    if category == "misc":
        return _misc_icon_specs(item_id)
    return _generic_icon_specs()


def _coin_icon_specs() -> list[IconSpec]:
    return [
        ((-0.022, 0.018, -0.006, 0.006), (-0.002, 0, 0.021), (0.74, 0.48, 0.11, 1.0)),
        ((-0.022, 0.020, -0.006, 0.006), (0.004, 0, 0.011), GOLD),
        ((-0.020, 0.022, -0.006, 0.006), (-0.004, 0, 0.001), (0.94, 0.68, 0.20, 1.0)),
        ((-0.010, 0.012, -0.002, 0.002), (0.002, 0, 0.012), (1.0, 0.90, 0.45, 1.0)),
    ]


def _misc_icon_specs(item_id: str) -> list[IconSpec]:
    if item_id == "wooden_splinters":
        return [
            ((-0.030, 0.030, -0.004, 0.004), (-0.010, 0, 0.005), (0.66, 0.48, 0.24, 1.0), 24),
            ((-0.028, 0.028, -0.004, 0.004), (0.010, 0, -0.006), (0.36, 0.20, 0.08, 1.0), -20),
            ((-0.020, 0.020, -0.003, 0.003), (0.000, 0, 0.020), (0.72, 0.51, 0.28, 1.0), 48),
        ]
    if item_id == "rusty_scrap":
        return [
            ((-0.025, 0.025, -0.017, 0.014), (-0.006, 0, 0.002), (0.76, 0.35, 0.15, 1.0), 14),
            ((-0.018, 0.018, -0.014, 0.014), (0.010, 0, 0.015), (0.16, 0.17, 0.18, 1.0), -20),
            ((-0.007, 0.007, -0.006, 0.006), (0.018, 0, -0.012), (0.78, 0.76, 0.68, 1.0)),
        ]
    if item_id == "glow_dust":
        return [
            ((-0.020, 0.020, -0.020, 0.020), (0.000, 0, 0.004), (0.18, 0.32, 0.58, 0.80)),
            ((-0.006, 0.006, -0.006, 0.006), (-0.013, 0, 0.018), (0.58, 0.72, 1.0, 1.0)),
            ((-0.005, 0.005, -0.005, 0.005), (0.012, 0, -0.012), (1.0, 0.88, 0.36, 1.0)),
            ((-0.004, 0.004, -0.004, 0.004), (0.018, 0, 0.022), (0.78, 0.90, 1.0, 1.0)),
        ]
    if item_id == "bones":
        return [
            ((-0.030, 0.030, -0.004, 0.004), (-0.006, 0, 0.006), (0.78, 0.72, 0.58, 1.0), 26),
            ((-0.006, 0.006, -0.006, 0.006), (-0.030, 0, -0.007), (0.78, 0.72, 0.58, 1.0)),
            ((-0.006, 0.006, -0.006, 0.006), (0.020, 0, 0.021), (0.78, 0.72, 0.58, 1.0)),
        ]
    if item_id == "cloth":
        return [
            ((-0.026, 0.026, -0.020, 0.018), (0.000, 0, 0.005), (0.66, 0.16, 0.09, 1.0), -12),
            ((-0.014, 0.014, -0.008, 0.008), (0.010, 0, 0.015), (0.78, 0.66, 0.44, 1.0), 10),
            ((-0.020, 0.020, -0.002, 0.002), (-0.004, 0, -0.018), (0.94, 0.72, 0.25, 1.0), 24),
        ]
    if item_id == "gel":
        return [
            ((-0.024, 0.024, -0.020, 0.020), (0.000, 0, 0.000), (0.22, 0.68, 0.26, 0.92)),
            ((-0.010, 0.010, -0.004, 0.004), (-0.007, 0, 0.018), (0.78, 1.0, 0.78, 0.90), -18),
        ]
    return _generic_icon_specs()


def _tool_icon_specs(item_id: str) -> list[IconSpec]:
    wood = (0.54, 0.30, 0.12, 1.0)
    metal, dark_metal, light_metal = _metal_palette(item_id)
    if "net" in item_id:
        return [
            ((-0.004, 0.004, -0.028, 0.028), (-0.015, 0, -0.006), wood, -34),
            ((-0.026, 0.026, -0.004, 0.004), (0.010, 0, 0.024), metal, 24),
            ((-0.020, 0.020, -0.004, 0.004), (0.010, 0, 0.024), light_metal, -24),
            ((-0.016, 0.016, -0.002, 0.002), (0.010, 0, 0.024), (0.78, 0.86, 0.84, 0.85), 0),
            ((-0.002, 0.002, -0.018, 0.018), (0.010, 0, 0.024), (0.78, 0.86, 0.84, 0.85), 90),
        ]
    if "fishing" in item_id or "rod" in item_id:
        return [
            ((-0.004, 0.004, -0.034, 0.034), (-0.004, 0, 0.010), wood, -22),
            ((-0.003, 0.003, -0.030, 0.020), (0.018, 0, 0.004), (0.82, 0.88, 0.86, 0.75), -10),
            ((-0.008, 0.008, -0.003, 0.003), (0.024, 0, -0.021), metal, 0),
            ((-0.010, 0.010, -0.002, 0.002), (0.014, 0, 0.041), light_metal, 0),
        ]
    if "pickaxe" in item_id:
        return [
            ((-0.004, 0.004, -0.032, 0.030), (0.000, 0, 0.004), wood, -26),
            ((-0.034, 0.034, -0.005, 0.005), (0.000, 0, 0.032), metal, 0),
            ((-0.035, -0.014, -0.004, 0.004), (-0.002, 0, 0.032), light_metal, -18),
            ((0.014, 0.035, -0.004, 0.004), (0.002, 0, 0.032), dark_metal, 18),
            ((-0.006, 0.006, -0.008, 0.008), (0.000, 0, 0.028), dark_metal, 0),
        ]
    if "pot" in item_id:
        return [
            ((-0.026, 0.026, -0.020, 0.020), (0.000, 0, 0.010), dark_metal),
            ((-0.022, 0.022, -0.016, 0.018), (0.000, 0, 0.014), metal),
            ((-0.030, 0.030, -0.004, 0.004), (0.000, 0, 0.034), light_metal),
            ((-0.018, 0.018, -0.003, 0.003), (0.000, 0, 0.042), dark_metal),
            ((-0.036, -0.026, -0.007, 0.007), (-0.002, 0, 0.018), dark_metal),
            ((0.026, 0.036, -0.007, 0.007), (0.002, 0, 0.018), dark_metal),
        ]
    return [
        ((-0.004, 0.004, -0.032, 0.030), (0.008, 0, 0.004), wood, -28),
        ((-0.030, 0.006, -0.016, 0.016), (-0.012, 0, 0.030), metal, -12),
        ((-0.032, -0.014, -0.010, 0.010), (-0.014, 0, 0.026), light_metal, -12),
        ((-0.020, -0.006, -0.008, 0.008), (-0.010, 0, 0.036), dark_metal, -12),
        ((-0.007, 0.007, -0.006, 0.006), (0.000, 0, 0.025), dark_metal),
    ]


def _weapon_icon_specs(item_id: str) -> list[IconSpec]:
    metal, dark_metal, light_metal = _metal_palette(item_id)
    wood = (0.54, 0.30, 0.12, 1.0)
    if "bow" in item_id:
        return [
            ((-0.004, 0.004, -0.034, 0.034), (-0.006, 0, 0.000), wood, -14),
            ((-0.003, 0.003, -0.028, 0.028), (0.014, 0, 0.000), (0.78, 0.86, 0.76, 0.80), 4),
            ((-0.024, 0.024, -0.003, 0.003), (0.004, 0, 0.014), light_metal, 0),
            ((-0.018, 0.018, -0.002, 0.002), (0.008, 0, -0.018), light_metal, 0),
        ]
    if "staff" in item_id:
        return [
            ((-0.005, 0.005, -0.036, 0.034), (0.000, 0, 0.000), wood, -8),
            ((-0.018, 0.018, -0.005, 0.005), (0.000, 0, 0.033), (0.34, 0.30, 0.72, 1.0), 0),
            ((-0.010, 0.010, -0.010, 0.010), (0.000, 0, 0.045), (0.58, 0.72, 1.0, 1.0), 0),
            ((-0.020, 0.020, -0.003, 0.003), (0.000, 0, -0.030), dark_metal, 0),
        ]
    return [
        ((-0.007, 0.007, -0.034, 0.034), (0.006, 0, 0.014), metal, -34),
        ((-0.003, 0.003, -0.030, 0.026), (0.001, 0, 0.018), light_metal, -34),
        ((-0.018, 0.018, -0.004, 0.004), (-0.010, 0, -0.010), (0.62, 0.42, 0.17, 1.0), -34),
        ((-0.005, 0.005, -0.018, 0.008), (-0.018, 0, -0.025), (0.36, 0.20, 0.08, 1.0), -34),
        ((-0.006, 0.006, -0.004, 0.006), (0.025, 0, 0.048), light_metal, -34),
        ((-0.006, 0.006, -0.012, 0.012), (-0.026, 0, -0.037), dark_metal, -34),
    ]


def _shield_icon_specs(item_id: str) -> list[IconSpec]:
    metal, dark_metal, light_metal = _metal_palette(item_id)
    return [
        ((-0.030, 0.030, -0.027, 0.024), (0.000, 0, 0.014), dark_metal),
        ((-0.024, 0.024, -0.026, 0.022), (0.000, 0, 0.017), metal),
        ((-0.016, 0.016, -0.020, 0.018), (0.000, 0, 0.012), light_metal),
        ((-0.004, 0.004, -0.024, 0.022), (0.000, 0, 0.016), dark_metal),
        ((-0.020, 0.020, -0.004, 0.004), (0.000, 0, 0.016), dark_metal),
        ((-0.010, 0.010, -0.010, 0.010), (0.000, 0, 0.018), (0.95, 0.77, 0.32, 1.0)),
        ((-0.018, 0.000, -0.003, 0.003), (-0.006, 0, 0.034), (1.0, 0.90, 0.48, 0.65), -18),
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
        "tin_ore": (0.62, 0.64, 0.62, 1.0),
        "iron_ore": (0.58, 0.32, 0.15, 1.0),
        "coal": (0.07, 0.07, 0.08, 1.0),
        "mithril_ore": (0.08, 0.34, 0.78, 1.0),
        "adamant_ore": (0.24, 0.68, 0.30, 1.0),
        "starsteel_ore": (0.46, 0.74, 1.0, 1.0),
    }.get(item_id, (0.52, 0.52, 0.48, 1.0))
    return [
        ((-0.026, 0.020, -0.020, 0.018), (-0.002, 0, 0.015), (0.18, 0.17, 0.15, 1.0)),
        ((-0.020, 0.024, -0.016, 0.020), (0.002, 0, 0.017), color),
        ((-0.010, 0.014, -0.007, 0.007), (0.000, 0, 0.026), (0.82, 0.80, 0.70, 0.65)),
        ((-0.020, -0.006, -0.006, 0.008), (-0.003, 0, 0.009), (0.06, 0.05, 0.04, 0.45)),
    ]


def _bar_icon_specs(item_id: str) -> list[IconSpec]:
    color, dark, light = _metal_palette(item_id.replace("_bar", "_sword"))
    return [
        ((-0.030, 0.030, -0.016, 0.016), (0.000, 0, 0.014), dark, -8),
        ((-0.025, 0.025, -0.011, 0.011), (0.000, 0, 0.018), color, -8),
        ((-0.018, 0.018, -0.003, 0.003), (0.002, 0, 0.026), light, -8),
        ((-0.020, 0.020, -0.002, 0.002), (-0.002, 0, 0.007), (0.08, 0.06, 0.04, 0.35), -8),
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
    return _metal_palette(item_id)[0]


def _metal_shadow_color(item_id: str) -> tuple[float, float, float, float]:
    return _metal_palette(item_id)[1]


def _metal_palette(item_id: str) -> tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]:
    if item_id.startswith("iron"):
        return (0.58, 0.32, 0.15, 1.0), (0.32, 0.18, 0.10, 1.0), (0.78, 0.48, 0.25, 1.0)
    if item_id.startswith("mithril"):
        return (0.08, 0.34, 0.78, 1.0), (0.04, 0.14, 0.34, 1.0), (0.28, 0.58, 0.96, 1.0)
    if item_id.startswith("starsteel"):
        return (0.46, 0.74, 1.0, 1.0), (0.20, 0.46, 0.70, 1.0), (0.76, 0.92, 1.0, 1.0)
    return (0.74, 0.46, 0.22, 1.0), (0.42, 0.24, 0.10, 1.0), (0.96, 0.68, 0.34, 1.0)


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


def _quantity_verb(action: str) -> str:
    return {
        "buy": "Buy",
        "sell": "Sell",
        "deposit": "Deposit",
        "withdraw": "Withdraw",
        "cook": "Cook",
        "smelt": "Smelt",
        "smith": "Smith",
    }.get(action, action.replace("_", " ").title())


def _skill_unlock_lines(
    skill_id: str,
    items_data: dict[str, dict[str, object]],
    world_data: dict[str, object],
    recipes_data: dict[str, object],
    skills: Any | None,
) -> list[str]:
    if skill_id in {"woodcutting", "mining", "fishing"}:
        return _resource_unlock_lines(skill_id, items_data, world_data)
    if skill_id == "cooking":
        return _cooking_unlock_lines(items_data, skills)
    if skill_id == "smithing":
        return _smithing_unlock_lines(items_data, recipes_data)
    if skill_id in {"attack", "strength", "defence", "ranged", "magic"}:
        return _equipment_unlock_lines(skill_id, items_data)
    if skill_id == "hitpoints":
        return _food_unlock_lines(items_data)
    return []


def _resource_unlock_lines(
    skill_id: str,
    items_data: dict[str, dict[str, object]],
    world_data: dict[str, object],
) -> list[str]:
    raw_nodes = world_data.get("resource_nodes", [])
    if not isinstance(raw_nodes, list):
        return []
    seen: set[tuple[int, str]] = set()
    lines: list[str] = []
    for node in raw_nodes:
        if not isinstance(node, dict) or node.get("skill_id") != skill_id:
            continue
        item_id = str(node.get("item_reward") or "")
        required_level = int(node.get("required_level", 1) or 1)
        key = (required_level, item_id)
        if key in seen:
            continue
        seen.add(key)
        source = str(node.get("display_name") or node.get("node_type") or "Resource")
        lines.append(f"Lv {required_level}: {_item_name(items_data, item_id)} - {source}")
    return sorted(lines, key=_line_level_sort)


def _cooking_unlock_lines(items_data: dict[str, dict[str, object]], skills: Any | None) -> list[str]:
    lines: list[str] = []
    current_level = _hud_skill_level(skills, "cooking")
    for item_id, definition in items_data.items():
        cooked_item_id = definition.get("cook_result")
        if not cooked_item_id:
            continue
        required_level = int(definition.get("cooking_required_level", 1) or 1)
        xp = int(definition.get("cooking_xp", 0) or 0)
        success = _cooking_success_percent(current_level, required_level)
        burn = 100 - success
        lines.append(
            f"Lv {required_level}: {_item_name(items_data, item_id)} -> {_item_name(items_data, str(cooked_item_id))}"
            f" ({xp} XP, {success}%/{burn}%)"
        )
    return sorted(lines, key=_line_level_sort)


def _smithing_unlock_lines(
    items_data: dict[str, dict[str, object]],
    recipes_data: dict[str, object],
) -> list[str]:
    lines: list[str] = []
    for action_type, verb in (("smelting", "Smelt"), ("smithing", "Smith")):
        raw_recipes = recipes_data.get(action_type, [])
        if not isinstance(raw_recipes, list):
            continue
        for recipe in raw_recipes:
            if not isinstance(recipe, dict):
                continue
            required_level = int(recipe.get("required_level", 1) or 1)
            output = _item_name(items_data, str(recipe.get("output_item_id") or ""))
            inputs = recipe.get("inputs", {})
            input_text = _input_text(items_data, inputs if isinstance(inputs, dict) else {})
            xp = int(recipe.get("xp_reward", 0) or 0)
            lines.append(f"Lv {required_level}: {verb} {output} from {input_text} ({xp} XP)")
    return sorted(lines, key=_line_level_sort)


def _equipment_unlock_lines(skill_id: str, items_data: dict[str, dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for item_id, definition in items_data.items():
        required_skills = definition.get("required_skills")
        if not isinstance(required_skills, dict) or skill_id not in required_skills:
            continue
        required_level = int(required_skills.get(skill_id, 1) or 1)
        lines.append(f"Lv {required_level}: Equip {_item_name(items_data, item_id)}")
    return sorted(lines, key=_line_level_sort)


def _food_unlock_lines(items_data: dict[str, dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for item_id, definition in items_data.items():
        heal_amount = int(definition.get("heal_amount", 0) or 0)
        if heal_amount > 0:
            lines.append(f"Heal {heal_amount}: {_item_name(items_data, item_id)}")
    return lines


def _input_text(items_data: dict[str, dict[str, object]], inputs: dict[object, object]) -> str:
    parts: list[str] = []
    for item_id, quantity in inputs.items():
        parts.append(f"{quantity} {_item_name(items_data, str(item_id))}")
    return ", ".join(parts) if parts else "materials"


def _hud_skill_level(skills: Any | None, skill_id: str) -> int:
    if skills is None:
        return 1
    if hasattr(skills, "level"):
        return int(skills.level(skill_id))
    state = skills.get(skill_id)
    return int(getattr(state, "level", 1))


def _cooking_success_percent(level: int, required_level: int) -> int:
    tier = 1 + max(0, required_level - 1) // 15
    chance = 0.70 + 0.02 * (level - required_level) - 0.03 * (tier - 1)
    chance = max(0.35, min(0.98, chance))
    return int(round(chance * 100))


def _line_level_sort(line: str) -> tuple[int, str]:
    if not line.startswith("Lv "):
        return (999, line)
    raw = line[3:].split(":", 1)[0]
    try:
        return (int(raw), line)
    except ValueError:
        return (999, line)


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


def _inventory_slot_views(
    items_data: dict[str, dict[str, object]],
    inventory: dict[str, int],
) -> list[_InventorySlotView]:
    views: list[_InventorySlotView] = []
    for item_id in _inventory_item_ids(items_data, inventory):
        quantity = int(inventory.get(item_id, 0))
        if quantity <= 0:
            continue
        if _is_non_stackable_inventory_item(items_data, item_id):
            for occurrence_index in range(quantity):
                views.append(_InventorySlotView(item_id, 1, False, occurrence_index))
                if len(views) >= INVENTORY_SLOT_COUNT:
                    return views
        else:
            views.append(_InventorySlotView(item_id, quantity, True, 0))
    return views


def _is_non_stackable_inventory_item(items_data: dict[str, dict[str, object]], item_id: str) -> bool:
    return is_non_stackable_item(items_data, item_id)


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
