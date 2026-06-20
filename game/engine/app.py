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
from game.systems.gathering import GatheringSystem, ResourceNodeState
from game.systems.inventory import Inventory
from game.systems.interaction import InteractionManager
from game.systems.shop import Shop
from game.systems.skills import Skills
from game.ui.login import LoginScreen
from game.ui.hud import Hud
from game.world.map import WorldMap
from game.world.time import GameTime


LOGGER = logging.getLogger(__name__)


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

        self.inventory = Inventory()
        self.bank = Bank()
        self.skills = Skills(self.skills_data)
        self.gathering = GatheringSystem(self.world_map.resource_nodes, self.inventory, self.skills)
        self.shop = Shop(self.items_data)
        self.coins = 0
        self.game_time = GameTime()

        self.player = Player(self.world_map.grid, self.world_map.player_start)
        self.player.render(self.render)

        camera_data = self.world_map.camera_start
        self.game_camera = GameCamera(
            self.camera,
            CameraState(
                center_x=float(camera_data.get("center_x", 15.0)),
                center_y=float(camera_data.get("center_y", 15.0)),
                heading=float(camera_data.get("heading", 45.0)),
                zoom=float(camera_data.get("zoom", 22.0)),
            ),
        )
        self.game_camera.apply()

        self.hud = Hud(
            self.items_data,
            self.skills_data,
            on_bank_close=self.close_bank,
            on_deposit_item=self.deposit_bank_item,
            on_withdraw_item=self.withdraw_bank_item,
            on_deposit_all=self.deposit_all_bank,
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
            self.gathering,
            open_bank=self.open_bank,
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
        self.interactions.update()
        self.game_time.update(dt)
        self._update_hud()
        return task.cont

    def on_mouse_wheel(self, direction: int) -> None:
        self.game_camera.zoom(direction * settings.CAMERA_ZOOM_STEP)

    def on_left_click(self) -> None:
        tile, _ = ground_tile_from_mouse(self, self.world_map.grid)
        if tile is None:
            self.set_feedback("No ground selected")
            return
        self.selected_text = f"Selected tile: {tile[0]}, {tile[1]}"
        self.interactions.move_to_tile(tile)

    def on_right_click(self) -> None:
        obj = object_from_mouse(self, self.world_map)
        if obj is None:
            tile, _ = ground_tile_from_mouse(self, self.world_map.grid)
            if tile is not None:
                self.selected_text = f"Selected tile: {tile[0]}, {tile[1]}"
            self.set_feedback("No object selected")
            return
        self.selected_text = f"Selected object: {obj.kind} ({obj.object_id})"
        self.interactions.interact_with(obj)

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
        return {
            "version": save.SAVE_VERSION,
            "username": self.current_username,
            "player": self.player.to_dict(),
            "inventory": self.inventory.to_dict(),
            "bank": self.bank.to_dict(),
            "coins": self.coins,
            "skills": self.skills.to_dict(),
            "chopped_trees": chopped_trees,
            "depleted_resources": depleted_resources,
            "time": time_state,
            "world": {
                "chopped_trees": chopped_trees,
                "depleted_resources": depleted_resources,
                "resource_nodes": resource_nodes,
                **time_state,
            },
            "camera": self.game_camera.to_dict(),
        }

    def _apply_save_state(self, state: dict[str, Any]) -> None:
        world_state = state.get("world", {})
        self.player.load_dict(state.get("player", {}))
        self.inventory = Inventory.from_dict(state.get("inventory", {}))
        self.bank = Bank.from_dict(state.get("bank", {}))
        self.skills.load_dict(state.get("skills", {}))
        self.coins = int(state.get("coins", self.coins))
        self.game_time.load_dict(state.get("time", world_state))
        self.game_camera.load_dict(state.get("camera", {}))
        resource_states = self._resource_states_from_save(state, world_state)
        self.gathering.inventory = self.inventory
        self.gathering.skills = self.skills
        self.gathering.load_dict(resource_states)
        self.world_map.apply_resource_states(self.gathering.states)
        self.interactions.inventory = self.inventory
        self.interactions.skills = self.skills
        self.interactions.gathering = self.gathering

    def open_bank(self) -> None:
        self.hud.open_bank()
        self._update_hud()
        self.set_feedback("Bank opened")

    def close_bank(self) -> None:
        self.hud.close_bank()

    def deposit_bank_item(self, item_id: str) -> None:
        deposited = self.bank.deposit(self.inventory, item_id)
        if deposited:
            self.set_feedback(f"Deposited {deposited} {self._item_name(item_id)}")
        else:
            self.set_feedback(f"No {self._item_name(item_id)} to deposit")
        self._update_hud()

    def withdraw_bank_item(self, item_id: str) -> None:
        withdrawn = self.bank.withdraw(self.inventory, item_id)
        if withdrawn:
            self.set_feedback(f"Withdrew {withdrawn} {self._item_name(item_id)}")
        else:
            self.set_feedback(f"No {self._item_name(item_id)} in bank")
        self._update_hud()

    def deposit_all_bank(self) -> None:
        deposited = self.bank.deposit_all(self.inventory)
        total = sum(deposited.values())
        if total:
            self.set_feedback(f"Deposited {total} items")
        else:
            self.set_feedback("No items to deposit")
        self._update_hud()

    def _update_hud(self) -> None:
        self.hud.update(
            account=self.current_username or "",
            time_text=self.game_time.display(),
            coins=self.coins,
            selected_text=self.selected_text,
            inventory=self.inventory.to_dict(),
            bank=self.bank.to_dict(),
            skills=self.skills,
        )

    def _add_coins(self, amount: int) -> None:
        self.coins += amount

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

    def _configure_window(self) -> None:
        props = WindowProperties()
        props.setTitle(settings.WINDOW_TITLE)
        props.setSize(*settings.WINDOW_SIZE)
        self.win.requestProperties(props)

    def _configure_lighting(self) -> None:
        ambient = AmbientLight("ambient")
        ambient.setColor((0.7, 0.7, 0.7, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        sun = DirectionalLight("sun")
        sun.setColor((0.8, 0.78, 0.65, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(45, -60, 0)
        self.render.setLight(sun_np)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
