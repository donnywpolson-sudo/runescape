from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from game import settings
from game.entities.player import Player
from game.systems.combat import CombatSystem
from game.systems.cooking import CookingSystem
from game.systems.gathering import GatheringSystem
from game.systems.inventory import Inventory
from game.systems.shop import Shop
from game.systems.smithing import SmithingSystem
from game.systems.skills import Skills
from game.world.grid import Tile
from game.world.map import WorldMap
from game.world.objects import WorldObject
from game.world.pathfinding import find_path


@dataclass(frozen=True)
class InteractionAction:
    action_id: str
    label: str


class InteractionManager:
    def __init__(
        self,
        world_map: WorldMap,
        player: Player,
        inventory: Inventory,
        skills: Skills,
        shop: Shop,
        add_coins: Callable[[int], None],
        feedback: Callable[[str], None],
        gathering: GatheringSystem | None = None,
        cooking: CookingSystem | None = None,
        combat: CombatSystem | None = None,
        smithing: SmithingSystem | None = None,
        open_bank: Callable[[], None] | None = None,
        open_shop: Callable[[], None] | None = None,
        train_combat: Callable[[], None] | None = None,
        talk_to_npc: Callable[[WorldObject], None] | None = None,
        on_cooking_result: Callable[[object], None] | None = None,
        on_smithing_result: Callable[[object], None] | None = None,
        on_combat_result: Callable[[object], None] | None = None,
    ) -> None:
        self.world_map = world_map
        self.player = player
        self.inventory = inventory
        self.skills = skills
        self.shop = shop
        self.add_coins = add_coins
        self.feedback = feedback
        self.gathering = gathering
        self.cooking = cooking
        self.combat = combat
        self.smithing = smithing
        self.open_bank = open_bank
        self.open_shop = open_shop
        self.train_combat = train_combat
        self.talk_to_npc = talk_to_npc
        self.on_cooking_result = on_cooking_result
        self.on_smithing_result = on_smithing_result
        self.on_combat_result = on_combat_result
        self.pending_object_id: str | None = None
        self.pending_action_id: str | None = None
        self.selected_item_id: str | None = None

    def move_to_tile(self, tile: Tile) -> None:
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        self._cancel_smithing()
        path = find_path(self.world_map.grid, self.player.tile, tile, self.world_map.blocked_tiles())
        if path is None:
            self.feedback("No path")
            return
        self.pending_object_id = None
        self.pending_action_id = None
        self.player.set_path(path)

    def interact_with(self, obj: WorldObject | None) -> None:
        actions = self.get_actions(obj)
        if obj is not None and actions:
            self.perform_action(actions[0].action_id, obj)
            return
        self._interact_default(obj)

    def get_actions(self, obj: WorldObject | None) -> list[InteractionAction]:
        if obj is None:
            return []
        actions: list[InteractionAction] = []
        if self._is_gatherable(obj):
            node = self.world_map.resource_node_for_object(obj)
            skill_id = node.skill_id if node is not None else obj.skill_id
            label = {"woodcutting": "Chop down", "mining": "Mine", "fishing": "Fish"}.get(skill_id, "Gather")
            actions.append(InteractionAction("gather", f"{label} {obj.display_name or obj.kind}"))
        elif obj.kind == "cooking_range":
            actions.append(InteractionAction("cook", "Cook"))
        elif obj.kind == "furnace":
            actions.append(InteractionAction("smelt", "Smelt"))
        elif obj.kind == "anvil":
            actions.append(InteractionAction("smith", "Smith"))
        elif obj.kind == "bank":
            actions.append(InteractionAction("bank", "Bank"))
        elif obj.kind == "shop":
            actions.append(InteractionAction("trade", "Trade"))
        elif obj.kind == "npc":
            actions.append(InteractionAction("talk", f"Talk-to {obj.display_name or 'NPC'}"))
        elif self._is_combatable(obj):
            actions.append(InteractionAction("attack", f"Attack {obj.display_name or obj.kind}"))
        elif obj.kind == "combat_dummy":
            actions.append(InteractionAction("train", "Train"))
        elif obj.kind == "ground_item":
            actions.append(InteractionAction("take", f"Take {self._item_name(obj.item_id)}"))
        actions.append(InteractionAction("examine", f"Examine {obj.display_name or obj.kind}"))
        actions.append(InteractionAction("cancel", "Cancel"))
        return actions

    def perform_action(self, action_id: str, obj: WorldObject | None) -> None:
        if obj is None or action_id == "cancel":
            return
        if action_id == "examine":
            self.feedback(self._examine_text(obj))
            return
        self._interact_default(obj, action_id)

    def _interact_default(self, obj: WorldObject | None, action_id: str | None = None) -> None:
        if obj is None:
            self._cancel_gathering()
            self._cancel_cooking()
            self._cancel_combat()
            self._cancel_smithing()
            self.feedback("Nothing to interact with")
            return
        if self._is_gatherable(obj):
            if self._in_range(obj.tile):
                self._perform(obj, action_id)
                return
            self._cancel_gathering()
            self._cancel_cooking()
            self._cancel_combat()
            self._cancel_smithing()
            path = self._path_to_adjacent(obj.tile)
            if path is None:
                self.feedback("No path")
                return
            self.pending_object_id = obj.object_id
            self.pending_action_id = action_id
            self.player.set_path(path)
            self.feedback(f"Walking to {obj.kind}")
            return
        if self._is_combatable(obj) or obj.kind == "ground_item":
            if self._in_range_for(obj):
                self._perform(obj, action_id)
                return
            self._cancel_gathering()
            self._cancel_cooking()
            self._cancel_combat()
            self._cancel_smithing()
            path = self._path_to_object(obj)
            if path is None:
                self.feedback("No path")
                return
            self.pending_object_id = obj.object_id
            self.pending_action_id = action_id
            self.player.set_path(path)
            self.feedback(f"Walking to {obj.kind}")
            return
        self._cancel_gathering()
        self._cancel_combat()
        if obj.kind != "cooking_range":
            self._cancel_cooking()
        if obj.kind not in {"furnace", "anvil"}:
            self._cancel_smithing()
        if self._in_range_for(obj):
            self._perform(obj, action_id)
            return

        path = self._path_to_adjacent(obj.tile)
        if path is None:
            self.feedback("No path")
            return
        self.pending_object_id = obj.object_id
        self.pending_action_id = action_id
        self.player.set_path(path)
        self.feedback(f"Walking to {obj.kind}")

    def select_inventory_item(self, item_id: str) -> None:
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        self._cancel_smithing()
        if self.inventory.count(item_id) <= 0:
            self.selected_item_id = None
            self.feedback(f"No {self._item_name(item_id)}")
            return
        self.selected_item_id = item_id
        self.feedback(f"Selected item: {self._item_name(item_id)}")

    def update(self) -> None:
        if self.gathering is not None:
            result = self.gathering.update()
            if result is not None:
                self.world_map.apply_resource_states(self.gathering.states)
                self.feedback(result.feedback)

        if self.cooking is not None:
            result = self.cooking.update()
            if result is not None:
                if (
                    result.raw_item_id is not None
                    and result.raw_item_id == self.selected_item_id
                    and self.inventory.count(result.raw_item_id) <= 0
                ):
                    self.selected_item_id = None
                self.feedback(result.feedback)
                if self.on_cooking_result is not None:
                    self.on_cooking_result(result)

        if self.smithing is not None:
            result = self.smithing.update()
            if result is not None:
                if (
                    result.item_id is not None
                    and self.selected_item_id is not None
                    and self.inventory.count(self.selected_item_id) <= 0
                ):
                    self.selected_item_id = None
                self.feedback(result.feedback)
                if self.on_smithing_result is not None:
                    self.on_smithing_result(result)

        if self.combat is not None:
            result = self.combat.update()
            if result is not None:
                self.world_map.apply_mob_states(self.combat.states)
                feedback = result.feedback
                if result.killed and result.mob_id is not None:
                    mob = self.combat.mobs.get(result.mob_id)
                    if mob is not None:
                        created = self.world_map.spawn_ground_drops(mob.position, result.drops)
                        if created:
                            feedback = f"{feedback}; drops appeared"
                self.feedback(feedback)
                if self.on_combat_result is not None:
                    self.on_combat_result(result)

        if self.pending_object_id is None or self.player.is_moving:
            return
        obj = self.world_map.get_object(self.pending_object_id)
        self.pending_object_id = None
        if obj is None:
            return
        if self._in_range_for(obj):
            action_id = self.pending_action_id
            self.pending_action_id = None
            self._perform(obj, action_id)
        else:
            self.feedback("Too far away")

    def _perform(self, obj: WorldObject, action_id: str | None = None) -> None:
        if self._is_gatherable(obj):
            self._perform_gathering(obj)
        elif obj.kind == "cooking_range":
            self._perform_cooking()
        elif obj.kind == "furnace":
            self._perform_smelting()
        elif obj.kind == "anvil":
            self._perform_smithing()
        elif obj.kind == "bank":
            if self.open_bank is None:
                self.feedback("Bank unavailable")
                return
            self.open_bank()
        elif obj.kind == "shop":
            if self.open_shop is None:
                self.feedback("Shop unavailable")
                return
            self.open_shop()
        elif self._is_combatable(obj):
            self._perform_combat(obj)
        elif obj.kind == "ground_item":
            self._perform_ground_item(obj)
        elif obj.kind == "npc":
            if self.talk_to_npc is None:
                self.feedback("Nothing happens")
                return
            self.talk_to_npc(obj)
        elif obj.kind == "combat_dummy":
            if self.train_combat is None:
                self.feedback("Nothing happens")
                return
            self.train_combat()
        else:
            self.feedback("Nothing happens")

    def _perform_gathering(self, obj: WorldObject) -> None:
        if self.gathering is None:
            self.feedback("Nothing happens")
            return
        self._cancel_cooking()
        self._cancel_combat()
        self._cancel_smithing()
        result = self.gathering.start_gather(
            obj.object_id,
            self.player.tile,
            self.world_map.grid,
            self.world_map.blocked_tiles(),
            allow_movement=False,
        )
        self.world_map.apply_resource_states(self.gathering.states)
        self.feedback(result.feedback)

    def _perform_cooking(self) -> None:
        if self.cooking is None:
            self.feedback("Select a raw fish first")
            return
        self._cancel_gathering()
        self._cancel_combat()
        self._cancel_smithing()
        result = self.cooking.start_cooking(self.selected_item_id)
        self.feedback(result.feedback)

    def _perform_smelting(self) -> None:
        if self.smithing is None:
            self.feedback("Select ore to smelt")
            return
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        result = self.smithing.start_smelting(self.selected_item_id)
        self.feedback(result.feedback)

    def _perform_smithing(self) -> None:
        if self.smithing is None:
            self.feedback("Select bars to smith")
            return
        self._cancel_gathering()
        self._cancel_cooking()
        self._cancel_combat()
        result = self.smithing.start_smithing(self.selected_item_id)
        self.feedback(result.feedback)

    def _perform_combat(self, obj: WorldObject) -> None:
        if self.combat is None:
            self.feedback("Nothing happens")
            return
        self._cancel_gathering()
        self._cancel_cooking()
        result = self.combat.start_attack(
            obj.object_id,
            self.player.tile,
            self.world_map.grid,
            self.world_map.blocked_tiles(),
        )
        self.world_map.apply_mob_states(self.combat.states)
        self.feedback(result.feedback)

    def _perform_ground_item(self, obj: WorldObject) -> None:
        picked_up = self.world_map.pickup_ground_item(obj.object_id)
        if picked_up is None:
            self.feedback("Nothing to pick up")
            return
        item_id, quantity = picked_up
        self.inventory.add(item_id, quantity)
        self.feedback(f"Picked up {quantity} {self._item_name(item_id)}")

    def _path_to_object(self, obj: WorldObject) -> list[Tile] | None:
        if obj.kind == "ground_item":
            blocked = self.world_map.blocked_tiles()
            if obj.tile not in blocked:
                path = find_path(self.world_map.grid, self.player.tile, obj.tile, blocked)
                if path is not None:
                    return path
        return self._path_to_adjacent(obj.tile)

    def _path_to_adjacent(self, target: Tile) -> list[Tile] | None:
        blocked = self.world_map.blocked_tiles()
        best_path: list[Tile] | None = None
        for candidate in self.world_map.grid.neighbors(target, diagonals=True):
            if candidate in blocked:
                continue
            path = find_path(self.world_map.grid, self.player.tile, candidate, blocked)
            if path is not None and (best_path is None or len(path) < len(best_path)):
                best_path = path
        return best_path

    def _in_range(self, tile: Tile) -> bool:
        distance = max(abs(self.player.tile[0] - tile[0]), abs(self.player.tile[1] - tile[1]))
        return 0 < distance <= settings.INTERACTION_RANGE

    def _in_range_for(self, obj: WorldObject) -> bool:
        distance = max(abs(self.player.tile[0] - obj.tile[0]), abs(self.player.tile[1] - obj.tile[1]))
        if obj.kind == "ground_item":
            return distance <= settings.INTERACTION_RANGE
        return 0 < distance <= settings.INTERACTION_RANGE

    def _is_gatherable(self, obj: WorldObject) -> bool:
        return self.gathering is not None and obj.object_id in self.gathering.nodes

    def _is_combatable(self, obj: WorldObject) -> bool:
        return self.combat is not None and obj.active and obj.object_id in self.combat.mobs

    def _cancel_gathering(self) -> None:
        if self.gathering is not None:
            self.gathering.cancel_pending()

    def _cancel_cooking(self) -> None:
        if self.cooking is not None:
            self.cooking.cancel_pending()

    def _cancel_combat(self) -> None:
        if self.combat is not None:
            self.combat.cancel_pending()

    def _cancel_smithing(self) -> None:
        if self.smithing is not None:
            self.smithing.cancel_pending()

    def _item_name(self, item_id: str) -> str:
        if self.cooking is not None:
            return str(self.cooking.item_definitions.get(item_id, {}).get("name") or item_id.replace("_", " "))
        definition = self.shop.item_definitions.get(item_id)
        if definition is not None:
            return str(definition.get("name") or item_id.replace("_", " "))
        return item_id.replace("_", " ")

    def _examine_text(self, obj: WorldObject) -> str:
        if obj.kind == "mob":
            return f"{obj.display_name}: level {obj.level}, {obj.hitpoints} HP"
        if obj.kind == "ground_item":
            return f"{obj.quantity} {self._item_name(obj.item_id)} on the ground"
        return obj.display_name or obj.kind.replace("_", " ").title()
