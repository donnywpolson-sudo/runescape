from __future__ import annotations

from game.ui import hud


class FakeWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.options = dict(kwargs)
        self.destroyed = False
        self.hidden = False
        self.text = self.options.get("text", "")
        self.pos = self.options.get("pos")
        self.bindings = {}

    def setText(self, text: str) -> None:
        self.text = text

    def get(self) -> str:
        return str(self.text)

    def setPos(self, *pos) -> None:
        self.pos = pos
        self.options["pos"] = pos

    def hide(self) -> None:
        self.hidden = True

    def show(self) -> None:
        self.hidden = False

    def destroy(self) -> None:
        self.destroyed = True

    def __getitem__(self, key: str):
        return self.options[key]

    def __setitem__(self, key: str, value) -> None:
        self.options[key] = value
        if key == "text":
            self.text = value
        elif key == "pos":
            self.pos = value

    def click(self) -> None:
        command = self.options.get("command")
        if command is not None:
            command()

    def bind(self, event, command, extraArgs=None) -> None:
        self.bindings[event] = (command, list(extraArgs or []))

    def trigger(self, event) -> None:
        command, extra_args = self.bindings[event]
        command(*extra_args, None)


class FakeOnscreenText(FakeWidget):
    ALLOWED_INIT_OPTIONS = {
        "align",
        "bg",
        "decal",
        "direction",
        "drawOrder",
        "fg",
        "font",
        "frame",
        "mayChange",
        "parent",
        "pos",
        "roll",
        "scale",
        "shadow",
        "shadowOffset",
        "sort",
        "style",
        "text",
        "wordwrap",
    }

    def __init__(self, *args, **kwargs) -> None:
        unknown_options = set(kwargs) - self.ALLOWED_INIT_OPTIONS
        if unknown_options:
            unknown = ", ".join(sorted(unknown_options))
            raise TypeError(f"unexpected OnscreenText option(s): {unknown}")
        super().__init__(*args, **kwargs)
        self.may_change = bool(self.options.get("mayChange")) or not self.text

    def setText(self, text: str) -> None:
        if not self.may_change:
            raise AssertionError("static OnscreenText cannot be changed")
        super().setText(text)

    def setPos(self, *pos) -> None:
        if not self.may_change:
            raise AssertionError("static OnscreenText cannot be repositioned")
        super().setPos(*pos)


def test_inventory_grid_has_fixed_slots_and_populates_in_category_order(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    assert len(ui.inventory_slots) == hud.INVENTORY_SLOT_COUNT
    assert all(not slot.button.hidden for slot in ui.inventory_slots)

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={
            "mystery_item": 1,
            "raw_shrimp": 4,
            "copper_ore": 6,
            "logs": 3,
            "coins": 12,
        },
        bank={},
        skills=FakeSkills(),
    )

    assert [slot.item_id for slot in ui.inventory_slots[:6]] == [
        "coins",
        "logs",
        "logs",
        "logs",
        "copper_ore",
        "copper_ore",
    ]
    assert ui.inventory_slots[0].button.text == "12"
    assert ui.inventory_slots[1].button.text == ""
    assert ui.inventory_slots[0].button.options["text_scale"] == hud.INVENTORY_QUANTITY_TEXT_SCALE
    assert any(not part.hidden for part in ui.inventory_slots[0].icon.parts)
    assert ui.inventory_slots[0].icon.label.text == "$"
    assert ui.inventory_slots[1].icon.label.hidden is True
    assert ui.inventory_slots[4].icon.label.hidden is True
    assert ui.inventory_slots[15].item_id is None
    assert ui.inventory_slots[15].button.text == ""
    assert all(part.hidden for part in ui.inventory_slots[15].icon.parts)
    assert ui.inventory_slots[15].icon.label.hidden is True


def test_misc_loot_icons_are_distinct() -> None:
    items = {
        "wooden_splinters": {"name": "Wooden splinters", "category": "misc"},
        "rusty_scrap": {"name": "Rusty scrap", "category": "misc"},
        "glow_dust": {"name": "Glow dust", "category": "misc"},
        "bones": {"name": "Bones", "category": "misc"},
        "cloth": {"name": "Cloth", "category": "misc"},
        "gel": {"name": "Gel", "category": "misc"},
    }

    icons = {item_id: tuple(hud._item_icon_specs(items, item_id)) for item_id in items}

    assert len(set(icons.values())) == len(items)


def test_inventory_expands_gear_and_tools_without_quantity_labels(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.update(
        account="test",
        time_text="Day 1 12:00",
        selected_text="Selected: none",
        inventory={"logs": 3, "bronze_axe": 2, "bronze_sword": 2, "bronze_shield": 2},
        bank={},
        skills=FakeSkills(),
    )

    assert [slot.item_id for slot in ui.inventory_slots[:7]] == [
        "bronze_axe",
        "bronze_axe",
        "bronze_sword",
        "bronze_sword",
        "bronze_shield",
        "bronze_shield",
        "logs",
    ]
    assert [slot.button.text for slot in ui.inventory_slots[:6]] == ["", "", "", "", "", ""]
    assert ui.inventory_slots[6].button.text == ""
    assert ui.inventory_slots[0].icon.label.hidden is True
    assert ui.inventory_slots[2].icon.label.hidden is True
    assert ui.inventory_slots[4].icon.label.hidden is True


def test_inventory_slot_hover_shows_item_name_without_world_hover_override(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())
    ui.set_feedback("Ready")
    ui.set_hover_text("Grass")
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"raw_shrimp": 4},
        bank={},
        skills=FakeSkills(),
    )

    ui.inventory_slots[0].button.trigger(hud.DGG.ENTER)

    assert ui.feedback.text == "Raw shrimp"

    ui.set_hover_text("Tree")

    assert ui.feedback.text == "Raw shrimp"

    ui.inventory_slots[0].button.trigger(hud.DGG.EXIT)

    assert ui.feedback.text == "Tree"


def test_inventory_slots_use_select_item_callback(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    selected: list[str] = []
    ui = hud.Hud(_items(), on_select_item=selected.append)
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"raw_shrimp": 4},
        bank={},
        skills=FakeSkills(),
    )

    ui.inventory_slots[0].button.click()
    ui.inventory_slots[4].button.click()

    assert selected == ["raw_shrimp"]


def test_duplicate_nonstackable_inventory_selection_uses_occurrence_index(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    selected: list[tuple[str, int]] = []
    ui = hud.Hud(
        {"bronze_bar": {"name": "Bronze bar", "category": "bar", "stackable": False}},
        on_select_item=lambda item_id, occurrence_index: selected.append((item_id, occurrence_index)),
    )

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"bronze_bar": 4},
        bank={},
        skills=FakeSkills(),
    )

    ui.inventory_slots[2].button.click()

    assert selected == [("bronze_bar", 2)]

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        selected_item_slot=("bronze_bar", 2),
        inventory={"bronze_bar": 4},
        bank={},
        skills=FakeSkills(),
    )

    assert ui.inventory_slots[0].button.options["frameColor"][0] == hud.SLOT
    assert ui.inventory_slots[2].button.options["frameColor"][0] == hud.SLOT_HILITE


def test_inventory_right_click_context_examines_or_drops_one_item(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    examined: list[str] = []
    dropped: list[str] = []
    ui = hud.Hud(_items(), on_examine_item=examined.append, on_drop_item=dropped.append)
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"raw_shrimp": 2},
        bank={},
        skills=FakeSkills(),
    )

    ui.inventory_slots[0].button.trigger(hud.DGG.B3PRESS)
    assert [button.text for button in ui.context_buttons] == ["Examine Raw shrimp", "Drop Raw shrimp", "Cancel"]
    ui.context_buttons[0].click()

    ui.inventory_slots[0].button.trigger(hud.DGG.B3PRESS)
    ui.context_buttons[1].click()

    assert examined == ["raw_shrimp"]
    assert dropped == ["raw_shrimp"]


def test_feedback_routes_to_chatbox_and_keeps_latest_messages(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    for index in range(10):
        ui.set_feedback(f"Message {index}")

    assert ui.feedback.text == "Message 9"
    assert ui.chat_messages == [f"Message {index}" for index in range(10)]
    assert [line.text for line in ui.chat_lines] == [f"Message {index}" for index in range(2, 10)]


def test_stats_panel_omits_selected_tile_and_item_text(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.update(
        account="test",
        time_text="Day 1 08:00\nHP: 10/10",
        selected_text="Selected tile: 18, 17",
        selected_item_id="raw_shrimp",
        inventory={"raw_shrimp": 1},
        bank={},
        skills=FakeSkills(),
    )

    assert ui.stats.text == "Account: test"
    assert "Day" not in ui.stats.text
    assert "HP" not in ui.stats.text
    assert "Selected" not in ui.stats.text
    assert ui.file_button.pos == (0.37, 0, -0.155)


def test_chat_log_scrolls_through_history_and_autofollows_latest(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    for index in range(12):
        ui.set_feedback(f"Message {index}")

    assert [line.text for line in ui.chat_lines] == [f"Message {index}" for index in range(4, 12)]

    ui.scroll_chat(2)
    assert ui.chat_scroll == 2
    assert [line.text for line in ui.chat_lines] == [f"Message {index}" for index in range(2, 10)]

    ui.set_feedback("Message 12")
    assert ui.chat_scroll == 3
    assert [line.text for line in ui.chat_lines] == [f"Message {index}" for index in range(2, 10)]

    ui.chat_down_button.click()
    assert ui.chat_scroll == 2
    assert [line.text for line in ui.chat_lines] == [f"Message {index}" for index in range(3, 11)]

    ui.scroll_chat(-99)
    ui.set_feedback("Message 13")
    assert ui.chat_scroll == 0
    assert [line.text for line in ui.chat_lines] == [f"Message {index}" for index in range(6, 14)]


def test_chat_history_is_capped_after_retaining_scrollback(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    for index in range(hud.CHAT_HISTORY_LIMIT + 5):
        ui.set_feedback(f"Message {index}")

    assert len(ui.chat_messages) == hud.CHAT_HISTORY_LIMIT
    assert ui.chat_messages[0] == "Message 5"
    assert ui.chat_messages[-1] == f"Message {hud.CHAT_HISTORY_LIMIT + 4}"


def test_quest_objective_panel_updates_and_marks_completion(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    assert ui.quest_panel.hidden is True

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        skills=FakeSkills(),
        quest_objective_text="Starter path 1/8: Smelt a bar.",
    )

    assert ui.quest_panel.hidden is False
    assert ui.quest_objective.text == "Starter path 1/8: Smelt a bar."
    assert ui.quest_objective.options["fg"] == hud.TEXT

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        skills=FakeSkills(),
        quest_objective_text="Starter path complete.",
        quest_objective_completed=True,
    )

    assert ui.quest_objective.text == "Starter path complete."
    assert ui.quest_objective.options["fg"] == hud.GOLD

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        skills=FakeSkills(),
    )

    assert ui.quest_panel.hidden is True
    assert ui.quest_objective.text == ""


def test_quantity_mode_caps_transaction_amount(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    assert ui.transaction_quantity(12) == 12

    ui.set_quantity_mode("5")
    assert ui.transaction_quantity(12) == 5
    assert ui.transaction_quantity(3) == 3

    ui.set_quantity_mode("10")
    assert ui.transaction_quantity(12) == 10

    ui.set_quantity_mode("bad")
    assert ui.transaction_quantity(12) == 10


def test_opening_shop_defaults_to_single_item_quantity(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.set_quantity_mode("all")
    ui.open_shop()

    assert ui.quantity_mode == "1"
    assert ui.transaction_quantity(12) == 1


def test_context_menu_dispatches_selected_action_and_hides(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    selected: list[str] = []
    ui = hud.Hud(_items())

    ui.show_context_menu(
        [("talk", "Talk-to Guide"), ("examine", "Examine Guide")],
        selected.append,
        pos=(0.12, 0, 0.22),
    )

    assert ui.context_panel.hidden is False
    assert ui.context_panel.pos == (0.12, 0, 0.22)
    assert [button.text for button in ui.context_buttons] == ["Talk-to Guide", "Examine Guide"]

    ui.context_buttons[0].click()

    assert selected == ["talk"]
    assert ui.context_panel.hidden is True
    assert ui.context_buttons == []


def test_context_menu_position_is_clamped(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.show_context_menu(
        [("walk", "Walk here")],
        lambda action_id: None,
        pos=(9.0, 0, -9.0),
    )

    assert ui.context_panel.pos == (hud.DEFAULT_VIEWPORT_ASPECT - 0.17, 0, -0.70)


def test_pointer_over_blocking_ui_covers_tabs_and_overlays(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    assert ui.pointer_over_blocking_ui((1.76, -0.99)) is True
    assert ui.pointer_over_blocking_ui((1.40, -0.30)) is True
    assert ui.pointer_over_blocking_ui((0.0, 0.91)) is True
    assert ui.pointer_over_blocking_ui((-0.20, 0.0)) is False

    ui.tab_buttons[hud.INVENTORY_TAB].click()
    assert ui.tabs_collapsed is True
    assert ui.pointer_over_blocking_ui((1.40, -0.30)) is False
    assert ui.pointer_over_blocking_ui((1.53, -0.95)) is True

    ui.open_bank()
    assert ui.pointer_over_blocking_ui((0.0, 0.0)) is True
    ui.close_bank()

    ui.open_shop()
    assert ui.pointer_over_blocking_ui((0.0, 0.0)) is True
    ui.close_shop()

    ui.show_context_menu([("walk", "Walk here")], lambda action_id: None, pos=(0.10, 0, 0.20))
    assert ui.pointer_over_blocking_ui((0.10, 0.20)) is True


def test_settings_menu_toggles_compact_tabs_and_closes_transients(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.file_button.click()
    assert ui.file_menu_open is True

    ui.settings_button.click()

    assert ui.file_menu_open is False
    assert ui.settings_menu_open is True
    assert ui.settings_menu.hidden is False
    assert ui.settings_compact_button.text == "Compact HUD: Off"

    ui.settings_compact_button.click()

    assert ui.tabs_collapsed is True
    assert ui.settings_compact_button.text == "Compact HUD: On"
    assert ui.tab_box.options["frameSize"] == hud.TAB_BOX_COLLAPSED_FRAME_SIZE
    settings_region = hud._region_for(ui.settings_menu)
    assert settings_region is not None
    assert ui.pointer_over_blocking_ui(
        ((settings_region[0] + settings_region[1]) / 2, (settings_region[2] + settings_region[3]) / 2)
    ) is True
    assert ui.close_transient_if_outside((0.90, 0.90)) is True
    assert ui.settings_menu_open is False
    assert ui.settings_menu.hidden is True


def test_viewport_layout_anchors_edge_panels(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.apply_viewport_layout(2.25)

    assert hud._region_for(ui.stats_panel)[0] == -2.25
    assert hud._region_for(ui.stats_panel)[3] == 1.0
    assert hud._region_for(ui.feedback_panel)[3] == 1.0
    assert hud._region_for(ui.quest_panel)[3] == hud._region_for(ui.feedback_panel)[2]
    assert hud._region_for(ui.chat_panel)[0] == -2.25
    assert hud._region_for(ui.chat_panel)[2] == -1.0
    assert hud._region_for(ui.minimap)[1] == 2.25
    assert hud._region_for(ui.minimap)[3] == 1.0
    assert hud._region_for(ui.tab_box)[1] == 2.25
    assert hud._region_for(ui.tab_box)[2] == -1.0


def test_side_tabs_switch_visible_content(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    assert ui.active_tab == hud.INVENTORY_TAB
    assert ui.tab_box.pos == hud.TAB_BOX_POS
    assert ui.tab_buttons[hud.INVENTORY_TAB].options["parent"] is ui.tab_box
    assert ui.tab_buttons[hud.INVENTORY_TAB].pos == (-0.145, 0, 0.005)
    assert ui.tab_buttons[hud.INVENTORY_TAB].options["frameSize"] == hud.TAB_BUTTON_FRAME_SIZE
    assert ui.tab_buttons[hud.SKILLS_TAB].pos == (0.0, 0, 0.005)
    assert ui.tab_buttons[hud.CLOTHES_TAB].pos == (0.145, 0, 0.005)
    assert ui.tab_frames[hud.INVENTORY_TAB].hidden is False
    assert ui.tab_frames[hud.CLOTHES_TAB].hidden is True
    assert ui.tab_frames[hud.SKILLS_TAB].hidden is True

    ui.tab_buttons[hud.SKILLS_TAB].click()

    assert ui.active_tab == hud.SKILLS_TAB
    assert ui.tab_frames[hud.INVENTORY_TAB].hidden is True
    assert ui.tab_frames[hud.CLOTHES_TAB].hidden is True
    assert ui.tab_frames[hud.SKILLS_TAB].hidden is False
    assert ui.tab_buttons[hud.SKILLS_TAB].options["frameColor"][0] == hud.SLOT_HILITE

    ui.tab_buttons[hud.SKILLS_TAB].click()

    assert ui.tabs_collapsed is True
    assert ui.tab_box.hidden is False
    assert ui.tab_box.options["frameSize"] == hud.TAB_BOX_COLLAPSED_FRAME_SIZE
    assert ui.tab_frames[hud.SKILLS_TAB].hidden is True


def test_loot_window_selects_one_stack_and_closes_as_transient(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    selected: list[str] = []
    ui = hud.Hud(_items())

    ui.show_loot_window(
        [("ground_item_0001", "Coins x3"), ("ground_item_0002", "Logs x1")],
        selected.append,
        (2, 2),
        pos=(9.0, 0, 9.0),
    )

    assert ui.loot_panel.hidden is False
    assert ui.loot_tile == (2, 2)
    assert [button.text for button in ui.loot_buttons] == ["Coins x3", "Logs x1"]

    ui.loot_buttons[1].click()

    assert selected == ["ground_item_0002"]
    assert ui.close_transient_if_outside((0.0, 0.0)) is True
    assert ui.loot_panel.hidden is True


def test_clothes_tab_shows_equipped_item_icons(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.update(
        account="test",
        time_text="Day 1 12:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        equipment={"weapon": "bronze_sword", "shield": "bronze_shield"},
        skills=FakeSkills(),
    )

    weapon_slot = ui.equipment_slots["weapon"]
    shield_slot = ui.equipment_slots["shield"]
    head_slot = ui.equipment_slots["head"]

    assert weapon_slot.button.text == ""
    assert weapon_slot.icon.label.hidden is True
    assert any(not part.hidden for part in weapon_slot.icon.parts)
    assert shield_slot.button.text == ""
    assert shield_slot.icon.label.hidden is True
    assert head_slot.button.text == "Head"
    assert head_slot.icon.label.hidden is True


def test_clothes_tab_selects_combat_training_style(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    selected: list[str] = []
    ui = hud.Hud(_items(), on_combat_style=selected.append)

    ui.update(
        account="test",
        time_text="Day 1 12:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        combat_style="strength",
        skills=FakeSkills(),
    )

    assert ui.combat_style_buttons["strength"].options["frameColor"][0] == hud.SLOT_HILITE
    assert ui.combat_style_buttons["attack"].options["frameColor"][0] == hud.BUTTON
    assert "ranged" in ui.combat_style_buttons
    assert "magic" in ui.combat_style_buttons

    ui.combat_style_buttons["magic"].click()

    assert selected == ["magic"]


def test_skills_tab_uses_larger_two_line_skill_rows(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        skills=FakeSkills(),
    )

    row = ui.skill_rows["woodcutting"]
    assert row.name_label.text == "Woodcutting"
    assert row.name_label.options["scale"] == hud.SKILL_NAME_TEXT_SCALE
    assert row.detail_label.text == "Level 1  0 XP"
    assert row.detail_label.options["scale"] == hud.SKILL_DETAIL_TEXT_SCALE
    assert ui.tab_buttons[hud.SKILLS_TAB].options["scale"] == hud.SIDE_TAB_TEXT_SCALE
    assert hud.STATS_TEXT_SCALE > 0.032
    assert hud.CHAT_TEXT_SCALE > 0.023
    assert hud.ROW_TEXT_SCALE > 0.019


def test_clicking_skill_icon_opens_unlock_detail_pane(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(
        _items(),
        {
            "woodcutting": {"display_name": "Woodcutting"},
            "cooking": {"display_name": "Cooking"},
        },
        world_data={
            "resource_nodes": [
                {
                    "skill_id": "woodcutting",
                    "required_level": 1,
                    "item_reward": "logs",
                    "display_name": "Tree",
                }
            ]
        },
    )
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        skills=FakeSkills(),
    )

    ui.skill_buttons["woodcutting"].click()

    assert ui.skill_detail_panel.hidden is False
    assert "Woodcutting" in ui.skill_detail_title.text
    assert ui.skill_detail_lines[0].text == "Lv 1: Logs - Tree"


def test_ranged_and_magic_skill_details_use_equipment_unlocks(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    items = {
        **_items(),
        "training_bow": {
            "name": "Training bow",
            "category": "weapon",
            "stackable": False,
            "equip_slot": "weapon",
            "required_skills": {"ranged": 1},
        },
        "training_staff": {
            "name": "Training staff",
            "category": "weapon",
            "stackable": False,
            "equip_slot": "weapon",
            "required_skills": {"magic": 1},
        },
    }
    ui = hud.Hud(items)
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={},
        bank={},
        skills=FakeSkills(),
    )

    ui.select_skill_detail("ranged")
    assert ui.skill_detail_lines[0].text == "Lv 1: Equip Training bow"

    ui.select_skill_detail("magic")
    assert ui.skill_detail_lines[0].text == "Lv 1: Equip Training staff"


def test_selected_inventory_slot_is_highlighted(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"raw_shrimp": 4, "logs": 3},
        bank={},
        selected_item_id="raw_shrimp",
        skills=FakeSkills(),
    )

    assert ui.inventory_slots[0].item_id == "logs"
    assert ui.inventory_slots[0].button.options["frameColor"][0] == hud.SLOT
    assert ui.inventory_slots[3].item_id == "raw_shrimp"
    assert ui.inventory_slots[3].button.options["frameColor"][0] == hud.SLOT_HILITE


def test_ore_icons_use_distinct_metal_palettes() -> None:
    items = {
        "tin_ore": {"name": "Tin ore", "category": "ore"},
        "iron_ore": {"name": "Iron ore", "category": "ore"},
        "mithril_ore": {"name": "Mithril ore", "category": "ore"},
        "starsteel_ore": {"name": "Starsteel ore", "category": "ore"},
    }

    assert hud._item_icon_specs(items, "tin_ore")[1][2] == (0.62, 0.64, 0.62, 1.0)
    assert hud._item_icon_specs(items, "iron_ore")[1][2] == (0.58, 0.32, 0.15, 1.0)
    assert hud._item_icon_specs(items, "mithril_ore")[1][2] == (0.08, 0.34, 0.78, 1.0)
    assert hud._item_icon_specs(items, "starsteel_ore")[1][2] == (0.46, 0.74, 1.0, 1.0)


def test_starsteel_icons_use_high_tier_palette() -> None:
    items = {
        "starsteel_ore": {"name": "Starsteel ore", "category": "ore"},
        "starsteel_bar": {"name": "Starsteel bar", "category": "bar"},
        "starsteel_sword": {"name": "Starsteel sword", "category": "weapon"},
    }

    assert hud._metal_color("starsteel_sword") == (0.46, 0.74, 1.0, 1.0)
    assert hud._item_icon_specs(items, "starsteel_ore")[1][2] == (
        0.46,
        0.74,
        1.0,
        1.0,
    )
    assert hud._item_icon_specs(items, "starsteel_bar")[1][2] == (
        0.46,
        0.74,
        1.0,
        1.0,
    )


def test_bronze_tool_icons_use_bronze_metal() -> None:
    items = {"bronze_axe": {"name": "Bronze axe", "category": "tool", "stackable": False, "tool_for": "woodcutting"}}

    specs = hud._item_icon_specs(items, "bronze_axe")

    colors = [spec[2] for spec in specs]
    assert hud._metal_color("bronze_axe") in colors
    assert hud._metal_shadow_color("bronze_axe") in colors


def test_shape_first_gear_icons_hide_text_labels(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.update(
        account="test",
        time_text="Day 1 12:00",
        selected_text="Selected: none",
        inventory={"bronze_axe": 1, "bronze_sword": 1, "bronze_shield": 1},
        bank={},
        skills=FakeSkills(),
    )

    assert all(ui.inventory_slots[index].icon.label.hidden for index in range(3))
    assert all(any(not part.hidden for part in ui.inventory_slots[index].icon.parts) for index in range(3))


def test_bank_rows_show_positive_inventory_or_bank_stacks(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)

    ui = hud.Hud(
        {
            "logs": {"name": "Logs", "category": "wood"},
            "copper_ore": {"name": "Copper ore", "category": "ore"},
        }
    )

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"logs": 3, "copper_ore": 6},
        bank={"logs": 0},
        skills=FakeSkills(),
    )

    assert list(ui.bank_rows) == []
    assert list(ui.bank_inventory_rows) == ["logs", "copper_ore"]
    assert ui.bank_inventory_rows["logs"].quantity_label.text == "Qty 3"
    assert ui.bank_inventory_rows["copper_ore"].quantity_label.text == "Qty 6"
    assert ui.empty_bank_label.hidden is False
    assert ui.empty_bank_inventory_label.hidden is True

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"logs": 3, "copper_ore": 6},
        bank={"logs": 2},
        skills=FakeSkills(),
    )

    assert list(ui.bank_rows) == ["logs"]
    assert list(ui.bank_inventory_rows) == ["logs", "copper_ore"]
    assert ui.bank_rows["logs"].quantity_label.text == "Qty 2"
    assert ui.empty_bank_label.hidden is True

    row = ui.bank_rows["logs"]
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"copper_ore": 6},
        bank={"logs": 0},
        skills=FakeSkills(),
    )

    assert list(ui.bank_rows) == []
    assert list(ui.bank_inventory_rows) == ["copper_ore"]
    assert row.quantity_label.destroyed is True
    assert ui.empty_bank_label.hidden is False


def test_bank_rows_use_larger_text_and_buttons(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud({"logs": {"name": "Logs", "category": "wood"}})

    ui.update(
        account="test",
        time_text="Day 1 12:00",
        selected_text="Selected: none",
        inventory={"logs": 3},
        bank={"logs": 2},
        skills=FakeSkills(),
    )

    row = ui.bank_rows["logs"]
    assert row.item_label.options["scale"] == hud.BANK_ROW_TEXT_SCALE
    assert row.quantity_label.options["scale"] == 0.023
    assert any(not part.hidden for part in row.icon.parts)


def test_shop_buy_tab_shows_simple_rows_and_quantity_context(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    bought: list[str] = []
    items = {
        **_items(),
        "bronze_axe": {"name": "Bronze axe", "category": "tool", "stackable": False, "sell_price": 8},
    }
    ui = hud.Hud(items, on_buy_item=bought.append)

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"coins": 30},
        bank={},
        skills=FakeSkills(),
        shop_stock=[{"item_id": "bronze_axe", "price": 25}],
    )

    assert list(ui.shop_rows) == ["bronze_axe"]
    assert any(not part.hidden for part in ui.shop_rows["bronze_axe"].icon.parts)
    assert ui.shop_rows["bronze_axe"].icon.label.hidden is True
    assert ui.shop_rows["bronze_axe"].quantity_label.hidden is True
    assert ui.shop_rows["bronze_axe"].price_label.text == "25"
    assert ui.shop_coin_label.text == "Coins: 30"
    assert not hasattr(ui.shop_rows["bronze_axe"], "action_button")

    ui.shop_rows["bronze_axe"].item_button.trigger(hud.DGG.B3PRESS)

    assert [button.text for button in ui.context_buttons] == [
        "Buy 1 Bronze axe",
        "Buy 5 Bronze axe",
        "Buy 10 Bronze axe",
        "Buy X Bronze axe",
        "Buy All Bronze axe",
    ]

    ui.context_buttons[1].click()

    assert ui.quantity_mode == "5"
    assert bought == ["bronze_axe"]

    ui.shop_rows["bronze_axe"].item_button.trigger(hud.DGG.B3PRESS)
    ui.context_buttons[3].click()
    assert ui.shop_amount_panel.hidden is False

    ui._submit_shop_amount("7")

    assert ui.quantity_mode == "7"
    assert bought == ["bronze_axe", "bronze_axe"]


def test_shop_sell_tab_shows_inventory_rows_and_quantity_context(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    sold: list[str] = []
    items = {
        **_items(),
        "bronze_axe": {"name": "Bronze axe", "category": "tool", "stackable": False, "sell_price": 8},
        "logs": {"name": "Logs", "category": "wood", "stackable": False, "sell_price": 3},
    }
    ui = hud.Hud(items, on_sell_item=sold.append)

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"coins": 30, "logs": 2},
        bank={},
        skills=FakeSkills(),
        shop_stock=[{"item_id": "bronze_axe", "price": 25}],
    )
    ui.select_shop_tab("sell")

    assert list(ui.shop_rows) == ["sell:logs"]
    assert ui.shop_rows["sell:logs"].quantity_label.text == "2"
    assert ui.shop_rows["sell:logs"].price_label.text == "3"

    ui.shop_rows["sell:logs"].item_button.trigger(hud.DGG.B3PRESS)

    assert [button.text for button in ui.context_buttons] == [
        "Sell 1 Logs",
        "Sell 5 Logs",
        "Sell 10 Logs",
        "Sell X Logs",
        "Sell All Logs",
    ]

    ui.context_buttons[4].click()

    assert sold == ["logs"]
    assert ui.quantity_mode == "2"


def test_quantity_prompt_closes_when_clicking_outside(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    chosen: list[int] = []
    ui = hud.Hud(_items())

    ui.show_quantity_menu("sell", "Logs", 10, chosen.append)
    ui.context_buttons[3].click()

    assert ui.shop_amount_panel.hidden is False
    assert ui.close_transient_if_outside((0.90, 0.90)) is True
    assert ui.shop_amount_panel.hidden is True
    assert chosen == []


def test_shop_sell_tab_empty_state_uses_mutable_label(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    items = {
        **_items(),
        "bronze_axe": {"name": "Bronze axe", "category": "tool", "stackable": False, "sell_price": 8},
    }
    ui = hud.Hud(items)

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"coins": 30},
        bank={},
        skills=FakeSkills(),
        shop_stock=[{"item_id": "bronze_axe", "price": 25}],
    )
    ui.select_shop_tab("sell")

    assert ui.empty_shop_label.options["mayChange"] is True
    assert ui.empty_shop_label.hidden is False
    assert ui.empty_shop_label.text == "Nothing to sell"


class FakeSkills:
    def get(self, _skill_name: str) -> FakeSkill:
        return FakeSkill()


class FakeSkill:
    level = 1
    xp = 0


def _install_hud_fakes(monkeypatch) -> None:
    monkeypatch.setattr(hud, "DirectFrame", FakeWidget)
    monkeypatch.setattr(hud, "DirectButton", FakeWidget)
    monkeypatch.setattr(hud, "DirectEntry", FakeWidget)
    monkeypatch.setattr(hud, "OnscreenText", FakeOnscreenText)


def _items() -> dict[str, dict[str, object]]:
    return {
        "coins": {"name": "Coins", "category": "currency", "stackable": True},
        "logs": {"name": "Logs", "category": "wood", "stackable": False},
        "copper_ore": {"name": "Copper ore", "category": "ore", "stackable": False},
        "raw_shrimp": {
            "name": "Raw shrimp",
            "category": "fish",
            "stackable": False,
            "cook_result": "cooked_shrimp",
        },
        "bronze_axe": {
            "name": "Bronze axe",
            "category": "tool",
            "stackable": False,
            "tool_for": "woodcutting",
        },
        "bronze_sword": {
            "name": "Bronze sword",
            "category": "weapon",
            "stackable": False,
            "equip_slot": "weapon",
        },
        "bronze_shield": {
            "name": "Bronze shield",
            "category": "armor",
            "stackable": False,
            "equip_slot": "shield",
        },
        "mystery_item": {"name": "Mystery item"},
    }
