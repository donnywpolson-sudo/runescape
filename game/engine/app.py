from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AmbientLight, DirectionalLight, WindowProperties

from game import settings
from game.engine.camera import CameraState, GameCamera
from game.engine.game_state import GameState
from game.engine.input import InputManager
from game.engine.logging_config import configure_logging
from game.engine.picking import ground_tile_from_mouse, object_from_mouse
from game.engine import save
from game.engine.validation import validate_data_dir
from game.entities.player import Player
from game.systems.bank import Bank
from game.systems.combat import CombatSystem
from game.systems.cooking import CookingSystem
from game.systems.equipment import Equipment
from game.systems.gathering import GatheringSystem, ResourceNodeState
from game.systems.inventory import COINS_ITEM_ID, Inventory
from game.systems.interaction import InteractionManager
from game.systems.quest import QuestSystem
from game.systems.shop import Shop
from game.systems.smithing import SmithingRecipe, SmithingSystem
from game.systems.skills import Skills
from game.ui.login import LoginScreen
from game.ui.hud import Hud
from game.style import WorldPalette as Palette
from game.world import visuals
from game.world.animation import SceneAnimator
from game.world.map import WorldMap
from game.world.time import GameTime


LOGGER = logging.getLogger(__name__)
DAYLIGHT_TINT = (1.0, 0.98, 0.90, 1.0)
DAYLIGHT_SKY = (0.56, 0.70, 0.84, 1.0)


class GameApp(ShowBase):
    def __init__(self) -> None:
        configure_logging()
        self.state = GameState.LOADING
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(0.52, 0.70, 0.88, 1)
        self._configure_window()
        self._configure_lighting()

        try:
            validate_data_dir(settings.DATA_DIR)
            self.items_data = _load_json(settings.DATA_DIR / "items.json")
            self.skills_data = _load_json(settings.DATA_DIR / "skills.json")
            self.world_data = _load_json(settings.DATA_DIR / "world.json")
            self.recipes_data = _load_json(settings.DATA_DIR / "recipes.json")
            quests_path = settings.DATA_DIR / "quests.json"
            self.quests_data = _load_json(quests_path) if quests_path.exists() else None
        except Exception:
            self.state = GameState.ERROR
            LOGGER.exception("Game data failed to load")
            raise

        self.current_username: str | None = None
        self.current_state: dict[str, Any] | None = None
        self.state = GameState.LOGIN
        self.login_screen = LoginScreen(self, self.enter_world)

    def enter_world(self, username: str, state: dict[str, Any], message: str) -> None:
        self.state = GameState.LOADING
        self.current_username = username
        self.current_state = state
        self._create_world()
        self._apply_save_state(state)
        self.state = GameState.PLAYING
        self.set_feedback(message)

    def _create_world(self) -> None:
        self.world_map = WorldMap(self.world_data)
        self.world_map.render(self.render)
        self._apply_fixed_world_light()

        self.inventory = Inventory()
        self.bank = Bank()
        self.skills = Skills(self.skills_data)
        self.equipment = Equipment(self.items_data, self.inventory, self.skills)
        self.gathering = GatheringSystem(self.world_map.resource_nodes, self.inventory, self.skills)
        self.cooking = CookingSystem(self.items_data, self.inventory, self.skills)
        self.smithing = SmithingSystem(self.recipes_data, self.inventory, self.skills)
        self.combat = CombatSystem(self.world_map.mob_definitions, skills=self.skills)
        self.quest = QuestSystem(self.quests_data)
        self.shop = Shop(self.items_data, self.world_map.shop_stock)
        self.game_time = GameTime()
        self.animator = SceneAnimator()

        self.player = Player(self.world_map.grid, self.world_map.player_start)
        self.player.render(self.render)
        self._create_world_markers()

        camera_data = self.world_map.camera_start
        self.game_camera = GameCamera(
            self.camera,
            CameraState(
                center_x=float(camera_data.get("center_x", 15.0)),
                center_y=float(camera_data.get("center_y", 15.0)),
                heading=float(camera_data.get("heading", 45.0)),
                zoom=float(camera_data.get("zoom", 22.0)),
            ),
            bounds_width=self.world_map.grid.width,
            bounds_height=self.world_map.grid.height,
        )
        self.game_camera.apply()

        self.hud = Hud(
            self.items_data,
            self.skills_data,
            on_bank_close=self.close_bank,
            on_deposit_item=self.deposit_bank_item,
            on_withdraw_item=self.withdraw_bank_item,
            on_deposit_all=self.deposit_all_bank,
            on_shop_close=self.close_shop,
            on_buy_item=self.buy_shop_item,
            on_sell_item=self.sell_inventory_item,
            on_sell_all=self.sell_all_shop_items,
            on_select_item=self.select_inventory_item,
            on_unequip_slot=self.unequip_slot,
            on_save=self.save_game,
            on_load=self.load_game,
            on_quit=self.userExit,
        )
        self.selected_text = "Selected: none"
        self.interactions = InteractionManager(
            self.world_map,
            self.player,
            self.inventory,
            self.skills,
            self.shop,
            self._add_coins,
            self.set_feedback,
            gathering=self.gathering,
            cooking=self.cooking,
            combat=self.combat,
            smithing=self.smithing,
            open_bank=self.open_bank,
            open_shop=self.open_shop,
            train_combat=self.train_combat,
            talk_to_npc=self.talk_to_npc,
            on_cooking_result=self.on_cooking_result,
            on_smithing_result=self.on_smithing_result,
            on_smithing_choice=self.show_smithing_choices,
            on_combat_result=self.on_combat_result,
            animator=self.animator,
        )

        self.input = InputManager(self)
        self.input.bind()
        self.taskMgr.add(self.update, "update")

    def update(self, task):
        dt = globalClock.getDt()
        self.game_camera.update_from_input(self.input.keys, dt)
        self.player.update(dt)
        self.gathering.refresh_all()
        self.world_map.apply_resource_states(self.gathering.states)
        self.combat.refresh_all()
        self.world_map.apply_mob_states(self.combat.states)
        self.interactions.update()
        self.animator.update(dt)
        self.game_time.update(dt)
        self._update_hover_marker()
        self._update_hud()
        self.hud.tick(dt)
        return task.cont

    def on_mouse_wheel(self, direction: int) -> None:
        self.game_camera.zoom(direction * settings.CAMERA_ZOOM_STEP)

    def on_left_click(self) -> None:
        if hasattr(self, "hud"):
            self.hud.hide_context_menu()
        obj = object_from_mouse(self, self.world_map)
        if obj is not None and obj.kind == "ground_item":
            self.selected_text = f"Selected object: {obj.kind} ({obj.object_id})"
            self._show_marker(self.destination_marker, obj.tile)
            self.interactions.interact_with(obj)
            return
        tile, _ = ground_tile_from_mouse(self, self.world_map.grid)
        if tile is None:
            self.set_feedback("No ground selected")
            return
        self.selected_text = f"Selected tile: {tile[0]}, {tile[1]}"
        self._show_marker(self.destination_marker, tile)
        self.interactions.move_to_tile(tile)

    def on_right_click(self) -> None:
        obj = object_from_mouse(self, self.world_map)
        if obj is None:
            tile, _ = ground_tile_from_mouse(self, self.world_map.grid)
            if tile is not None:
                self.selected_text = f"Selected tile: {tile[0]}, {tile[1]}"
                self._show_marker(self.selection_marker, tile)
            self.set_feedback("No object selected")
            return
        self.selected_text = f"Selected object: {obj.kind} ({obj.object_id})"
        self._show_marker(self.selection_marker, obj.tile)
        actions = [(action.action_id, action.label) for action in self.interactions.get_actions(obj)]
        self.hud.show_context_menu(actions, lambda action_id, object_id=obj.object_id: self._perform_context_action(object_id, action_id))

    def _perform_context_action(self, object_id: str, action_id: str) -> None:
        obj = self.world_map.get_object(object_id)
        if obj is None:
            self.set_feedback("Nothing to interact with")
            return
        self.interactions.perform_action(action_id, obj)

    def show_smithing_choices(self, action_type: str, recipes: list[SmithingRecipe]) -> None:
        actions = [(recipe.recipe_id, recipe.display_name) for recipe in recipes]
        self.hud.show_context_menu(
            actions,
            lambda recipe_id, action_type=action_type: self.interactions.start_smithing_recipe(action_type, recipe_id),
        )

    def save_game(self) -> None:
        if self.current_username is None:
            self.set_feedback("Login required")
            return

        try:
            self.current_state = self._build_save_state()
            save.save_game(self.current_username, self.current_state, settings.SAVES_DIR)
        except (OSError, ValueError) as exc:
            LOGGER.exception("Save failed")
            self.set_feedback(f"Save failed: {exc}")
            return
        self.set_feedback("Game saved")

    def load_game(self) -> None:
        if self.current_username is None:
            self.set_feedback("Login required")
            return

        try:
            state, created = save.load_or_create_save(self.current_username, settings.SAVES_DIR)
        except (OSError, ValueError) as exc:
            LOGGER.exception("Load failed")
            self.set_feedback(f"Load failed: {exc}")
            return
        self.current_state = state
        self._apply_save_state(state)
        self.set_feedback("New character created" if created else "Save loaded")

    def set_feedback(self, message: str) -> None:
        if hasattr(self, "hud"):
            self.hud.set_feedback(message)
        elif hasattr(self, "login_screen"):
            self.login_screen.set_status(message)

    def _build_save_state(self) -> dict[str, Any]:
        chopped_trees = sorted(self.world_map.chopped_tree_ids)
        depleted_resources = sorted(self.world_map.depleted_resource_ids)
        time_state = self.game_time.to_dict()
        resource_nodes = self.gathering.to_dict()
        combat_state = {
            "current_hitpoints": self.combat.current_hitpoints,
            "mobs": self.combat.to_dict(),
            "ground_items": self.world_map.ground_items_to_dict(),
        }
        quest_state = self.quest.to_dict()
        return {
            "version": save.SAVE_VERSION,
            "username": self.current_username,
            "player": self.player.to_dict(),
            "inventory": self.inventory.to_dict(),
            "bank": self.bank.to_dict(),
            "equipment": self.equipment.to_dict(),
            "skills": self.skills.to_dict(),
            "combat": combat_state,
            "quest_state": quest_state,
            "chopped_trees": chopped_trees,
            "depleted_resources": depleted_resources,
            "time": time_state,
            "world": {
                "chopped_trees": chopped_trees,
                "depleted_resources": depleted_resources,
                "resource_nodes": resource_nodes,
                "combat": combat_state,
                "quest_state": quest_state,
                **time_state,
            },
            "camera": self.game_camera.to_dict(),
        }

    def _apply_save_state(self, state: dict[str, Any]) -> None:
        state = save.migrate_save_state(state)
        if hasattr(self, "animator"):
            self.animator.stop_all()
        world_state = state.get("world", {})
        self.player.load_dict(state.get("player", {}))
        self.inventory = Inventory.from_dict(state.get("inventory", {}))
        self.bank = Bank.from_dict(state.get("bank", {}))
        self.skills.load_dict(state.get("skills", {}))
        self.equipment.inventory = self.inventory
        self.equipment.skills = self.skills
        self.equipment.load_dict(state.get("equipment", {}))
        self._sync_combat_bonuses()
        self.game_time.load_dict(state.get("time", world_state))
        self.game_camera.load_dict(state.get("camera", {}))
        resource_states = self._resource_states_from_save(state, world_state)
        self.gathering.inventory = self.inventory
        self.gathering.skills = self.skills
        self.gathering.load_dict(resource_states)
        self.cooking.inventory = self.inventory
        self.cooking.skills = self.skills
        self.cooking.cancel_pending()
        self.smithing.inventory = self.inventory
        self.smithing.skills = self.skills
        self.smithing.cancel_pending()
        combat_state = self._combat_state_from_save(state, world_state)
        self.combat.skills = self.skills
        self.combat.load_player_hitpoints(combat_state.get("current_hitpoints"))
        self.combat.load_dict(combat_state.get("mobs", {}))
        self.quest.load_dict(self._quest_state_from_save(state, world_state))
        self.world_map.apply_resource_states(self.gathering.states)
        self.world_map.apply_mob_states(self.combat.states)
        ground_items = combat_state.get("ground_items", [])
        self.world_map.load_ground_items(ground_items if isinstance(ground_items, list) else [])
        self.interactions.inventory = self.inventory
        self.interactions.skills = self.skills
        self.interactions.gathering = self.gathering
        self.interactions.cooking = self.cooking
        self.interactions.smithing = self.smithing
        self.interactions.combat = self.combat

    def open_bank(self) -> None:
        self.hud.close_shop()
        self.hud.open_bank()
        self._update_hud()
        self.set_feedback("Bank opened")

    def close_bank(self) -> None:
        self.hud.close_bank()

    def open_shop(self) -> None:
        self.hud.close_bank()
        self.hud.open_shop()
        self._update_hud()
        self.set_feedback("Shop opened")

    def close_shop(self) -> None:
        self.hud.close_shop()

    def deposit_bank_item(self, item_id: str) -> None:
        quantity = self.hud.transaction_quantity(self.inventory.count(item_id))
        deposited = self.bank.deposit(self.inventory, item_id, quantity) if quantity else 0
        if deposited:
            self.quest.record("used_bank")
            self.set_feedback(f"Deposited {deposited} {self._item_name(item_id)}")
        else:
            self.set_feedback(f"No {self._item_name(item_id)} to deposit")
        self._update_hud()

    def withdraw_bank_item(self, item_id: str) -> None:
        quantity = self.hud.transaction_quantity(self.bank.count(item_id))
        withdrawn = self.bank.withdraw(self.inventory, item_id, quantity) if quantity else 0
        if withdrawn:
            self.quest.record("used_bank")
            self.set_feedback(f"Withdrew {withdrawn} {self._item_name(item_id)}")
        else:
            self.set_feedback(f"No {self._item_name(item_id)} in bank")
        self._update_hud()

    def deposit_all_bank(self) -> None:
        deposited = self.bank.deposit_all(self.inventory)
        total = sum(deposited.values())
        if total:
            self.quest.record("used_bank")
            self.set_feedback(f"Deposited {total} items")
        else:
            self.set_feedback("No items to deposit")
        self._update_hud()

    def sell_inventory_item(self, item_id: str) -> None:
        quantity = self.hud.transaction_quantity(self.inventory.count(item_id))
        sold, coins = self.shop.sell_item(self.inventory, item_id, quantity) if quantity else (0, 0)
        if sold:
            self.quest.record("used_shop")
            self._add_coins(coins)
            if self.interactions.selected_item_id == item_id and self.inventory.count(item_id) <= 0:
                self.interactions.selected_item_id = None
            self.set_feedback(f"Sold {sold} {self._item_name(item_id)} for {coins} coins")
        else:
            self.set_feedback(f"No sellable {self._item_name(item_id)}")
        self._update_hud()

    def buy_shop_item(self, item_id: str) -> None:
        stock_item = self.shop.stock.get(item_id)
        affordable = self.inventory.count(COINS_ITEM_ID) // stock_item.price if stock_item is not None else 0
        quantity = self.hud.transaction_quantity(affordable)
        result = self.shop.buy(self.inventory, item_id, quantity) if quantity else self.shop.buy(self.inventory, item_id, 1)
        if result.success:
            self.quest.record("used_shop")
        self.set_feedback(result.feedback)
        self._update_hud()

    def sell_all_shop_items(self) -> None:
        sold, coins = self.shop.sell_all(self.inventory)
        if sold:
            self.quest.record("used_shop")
            self._add_coins(coins)
            if self.interactions.selected_item_id and self.inventory.count(self.interactions.selected_item_id) <= 0:
                self.interactions.selected_item_id = None
            self.set_feedback(f"Sold {sold} items for {coins} coins")
        else:
            self.set_feedback("No sellable items")
        self._update_hud()

    def select_inventory_item(self, item_id: str) -> None:
        definition = self.items_data.get(item_id, {})
        heal_amount = int(definition.get("heal_amount", 0) or 0)
        if heal_amount > 0:
            self.eat_food(item_id, heal_amount)
        elif self.equipment.is_equippable(item_id):
            result = self.equipment.equip(item_id)
            self.set_feedback(result.feedback)
            if result.success and definition.get("equip_slot") == "weapon":
                self.quest.record("equipped_weapon")
            if result.success and self.interactions.selected_item_id == item_id and self.inventory.count(item_id) <= 0:
                self.interactions.selected_item_id = None
            if result.success:
                self._sync_combat_bonuses()
        else:
            self.interactions.select_inventory_item(item_id)
        self._update_hud()

    def eat_food(self, item_id: str, heal_amount: int) -> None:
        if self.inventory.count(item_id) <= 0:
            self.set_feedback(f"No {self._item_name(item_id)}")
            return
        healed = self.combat.heal(heal_amount)
        self.inventory.remove(item_id, 1)
        self.quest.record("ate_food")
        self.set_feedback(f"Ate {self._item_name(item_id)}: healed {healed} HP")

    def unequip_slot(self, slot: str) -> None:
        result = self.equipment.unequip(slot)
        self.set_feedback(result.feedback)
        if result.success:
            self._sync_combat_bonuses()
        self._update_hud()

    def train_combat(self) -> None:
        xp = 20
        for skill_id in ("attack", "strength", "defence"):
            self.skills.add_xp(skill_id, xp)
        self.set_feedback("Trained combat: +20 attack XP, +20 strength XP, +20 defence XP")
        self._update_hud()

    def talk_to_npc(self, obj) -> None:
        if obj.quest_id == "starter_path":
            result = self.quest.talk_to_starter()
            self._apply_quest_rewards(result)
            self.set_feedback(result.feedback)
            self._update_hud()
            return
        self.set_feedback(f"{obj.display_name}: Hello.")

    def _apply_quest_rewards(self, result: object) -> None:
        for reward in getattr(result, "item_rewards", ()):
            self.inventory.add(reward.item_id, reward.quantity)
        for reward in getattr(result, "skill_rewards", ()):
            self.skills.add_xp(reward.skill_id, reward.xp)

    def on_cooking_result(self, result: object) -> None:
        if getattr(result, "success", False) and getattr(result, "cooked_item_id", None):
            self.quest.record("cooked_food")

    def on_smithing_result(self, result: object) -> None:
        if not getattr(result, "success", False):
            return
        item_id = str(getattr(result, "item_id", "") or "")
        if item_id.endswith("_bar"):
            self.quest.record("smelted_bar")
        elif item_id:
            self.quest.record("smithed_gear")

    def on_combat_result(self, result: object) -> None:
        if getattr(result, "killed", False):
            self.quest.record("defeated_enemy")
        if getattr(result, "player_dead", False):
            self.player.set_position_tile(self.world_map.player_start)
            self.combat.reset_player()
            self.set_feedback(
                f"You died and respawned at the crossroads. HP restored to "
                f"{self.combat.current_hitpoints}/{self.combat.max_hitpoints()}."
            )
        self._update_hud()

    def _update_hud(self) -> None:
        objective = self.quest.current_objective()
        self.hud.update(
            account=self.current_username or "",
            time_text=f"{self.game_time.display()}\nHP: {self.combat.current_hitpoints}/{self.combat.max_hitpoints()}",
            selected_item_id=self.interactions.selected_item_id,
            inventory=self.inventory.to_dict(),
            bank=self.bank.to_dict(),
            equipment=self.equipment.to_dict(),
            skills=self.skills,
            selected_text=self.selected_text,
            shop_stock=[stock_item.__dict__ for stock_item in self.shop.stock_items()],
            gather_progress=self._activity_progress(),
            quest_objective_text=objective.text,
            quest_objective_completed=objective.completed,
        )

    def _add_coins(self, amount: int) -> None:
        if amount > 0:
            self.inventory.add(COINS_ITEM_ID, amount)

    def _sync_combat_bonuses(self) -> None:
        equipment = self.equipment.to_dict()
        weapon = self.items_data.get(equipment.get("weapon", ""), {})
        shield = self.items_data.get(equipment.get("shield", ""), {})
        self.combat.damage_per_hit = max(
            1,
            1 + int(weapon.get("attack_bonus", 0) or 0) + int(weapon.get("strength_bonus", 0) or 0),
        )
        self.combat.defence_bonus = int(shield.get("defence_bonus", 0) or 0)

    def _item_name(self, item_id: str) -> str:
        definition = self.items_data.get(item_id, {})
        return str(definition.get("name") or item_id.replace("_", " "))

    def _depleted_resources_from_save(
        self,
        state: dict[str, Any],
        world_state: dict[str, Any],
    ) -> list[str]:
        direct = state.get("depleted_resources", world_state.get("depleted_resources"))
        if isinstance(direct, list):
            return [str(resource_id) for resource_id in direct]

        legacy_nodes = world_state.get("resource_nodes")
        if isinstance(legacy_nodes, dict):
            return [
                str(resource_id)
                for resource_id, resource_state in legacy_nodes.items()
                if isinstance(resource_state, dict) and resource_state.get("depleted")
            ]

        legacy_trees = state.get("chopped_trees", world_state.get("chopped_trees", []))
        if isinstance(legacy_trees, list):
            return [str(resource_id) for resource_id in legacy_trees]
        return []

    def _resource_states_from_save(
        self,
        state: dict[str, Any],
        world_state: dict[str, Any],
    ) -> dict[str, dict[str, object]]:
        resource_nodes = world_state.get("resource_nodes")
        if isinstance(resource_nodes, dict):
            return {
                str(resource_id): resource_state
                for resource_id, resource_state in resource_nodes.items()
                if isinstance(resource_state, dict)
            }
        return {
            resource_id: ResourceNodeState(depleted=True, respawn_at=None).to_dict()
            for resource_id in self._depleted_resources_from_save(state, world_state)
        }

    def _combat_state_from_save(
        self,
        state: dict[str, Any],
        world_state: dict[str, Any],
    ) -> dict[str, Any]:
        combat_state = state.get("combat", world_state.get("combat", {}))
        return combat_state if isinstance(combat_state, dict) else {}

    def _quest_state_from_save(
        self,
        state: dict[str, Any],
        world_state: dict[str, Any],
    ) -> dict[str, Any]:
        quest_state = state.get("quest_state", world_state.get("quest_state", {}))
        return quest_state if isinstance(quest_state, dict) else {}

    def _configure_window(self) -> None:
        props = WindowProperties()
        props.setTitle(settings.WINDOW_TITLE)
        props.setSize(*settings.WINDOW_SIZE)
        if hasattr(self.win, "requestProperties"):
            self.win.requestProperties(props)

    def _configure_lighting(self) -> None:
        ambient = AmbientLight("ambient")
        ambient.setColor((0.62, 0.58, 0.50, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        sun = DirectionalLight("sun")
        sun.setColor((0.92, 0.82, 0.62, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(45, -60, 0)
        self.render.setLight(sun_np)

    def _create_world_markers(self) -> None:
        self.hover_marker = visuals.make_tile_marker("hover_marker", (1.0, 0.88, 0.46, 1.0), radius=0.43)
        self.selection_marker = visuals.make_tile_marker("selection_marker", Palette.RESOURCE_RING, radius=0.48)
        self.destination_marker = visuals.make_tile_marker("destination_marker", (0.48, 0.78, 1.0, 1.0), radius=0.38)
        for marker in (self.hover_marker, self.selection_marker, self.destination_marker):
            marker.reparentTo(self.render)

    def _update_hover_marker(self) -> None:
        if not hasattr(self, "hover_marker"):
            return
        tile, _ = ground_tile_from_mouse(self, self.world_map.grid)
        if tile is None:
            self.hover_marker.hide()
            self.hud.set_hover_text("")
            return
        self._show_marker(self.hover_marker, tile)
        self.hud.set_hover_text(self._hover_label(tile))

    def _show_marker(self, marker, tile: tuple[int, int]) -> None:
        x, y = self.world_map.grid.to_world(tile)
        marker.setPos(x, y, 0.045)
        marker.show()

    def _apply_fixed_world_light(self) -> None:
        self.render.setColorScale(*DAYLIGHT_TINT)
        self.setBackgroundColor(*DAYLIGHT_SKY)

    def _activity_progress(self) -> float | None:
        pending = self.gathering.pending
        remaining_seconds = self.gathering.remaining_seconds
        if pending is None:
            pending = self.cooking.pending
            remaining_seconds = self.cooking.remaining_seconds
        if pending is None:
            pending = self.smithing.pending
            remaining_seconds = self.smithing.remaining_seconds
        if pending is None:
            pending = self.combat.pending
            remaining_seconds = self.combat.remaining_seconds
        if pending is None or pending.duration <= 0:
            return None
        remaining = remaining_seconds()
        return max(0.0, min(1.0, (pending.duration - remaining) / pending.duration))

    def _hover_label(self, tile: tuple[int, int]) -> str:
        obj = self.world_map.object_at(tile)
        if obj is not None:
            if obj.is_resource_node and obj.depleted:
                return _display_label(obj.kind)
            node = self.world_map.resource_node_for_object(obj)
            if node is not None:
                return node.display_name or _display_label(node.node_type)
            if obj.kind == "ground_item":
                return f"{obj.quantity} {self._item_name(obj.item_id)}"
            if obj.kind == "mob":
                return f"{obj.display_name} (level {obj.level})"
            return obj.display_name or _display_label(obj.kind)

        decoration = self.world_map.decoration_at(tile)
        if decoration is not None:
            return _display_label(decoration.kind)
        return self.world_map.terrain_label(tile)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_label(value: str) -> str:
    return value.replace("_", " ").title()
