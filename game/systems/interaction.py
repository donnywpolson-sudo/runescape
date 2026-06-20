from __future__ import annotations

from collections.abc import Callable

from game import settings
from game.entities.player import Player
from game.systems.gathering import GatheringSystem
from game.systems.inventory import Inventory
from game.systems.shop import Shop
from game.systems.skills import Skills
from game.world.grid import Tile
from game.world.map import WorldMap
from game.world.objects import WorldObject
from game.world.pathfinding import find_path


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
        open_bank: Callable[[], None] | None = None,
    ) -> None:
        self.world_map = world_map
        self.player = player
        self.inventory = inventory
        self.skills = skills
        self.shop = shop
        self.add_coins = add_coins
        self.feedback = feedback
        self.gathering = gathering
        self.open_bank = open_bank
        self.pending_object_id: str | None = None

    def move_to_tile(self, tile: Tile) -> None:
        self._cancel_gathering()
        path = find_path(self.world_map.grid, self.player.tile, tile, self.world_map.blocked_tiles())
        if path is None:
            self.feedback("No path")
            return
        self.pending_object_id = None
        self.player.set_path(path)
        self.feedback(f"Moving to {tile[0]}, {tile[1]}")

    def interact_with(self, obj: WorldObject | None) -> None:
        if obj is None:
            self._cancel_gathering()
            self.feedback("Nothing to interact with")
            return
        if self._is_gatherable(obj):
            if self._in_range(obj.tile):
                self._perform(obj)
                return
            self._cancel_gathering()
            path = self._path_to_adjacent(obj.tile)
            if path is None:
                self.feedback("No path")
                return
            self.pending_object_id = obj.object_id
            self.player.set_path(path)
            self.feedback(f"Walking to {obj.kind}")
            return
        self._cancel_gathering()
        if self._in_range(obj.tile):
            self._perform(obj)
            return

        path = self._path_to_adjacent(obj.tile)
        if path is None:
            self.feedback("No path")
            return
        self.pending_object_id = obj.object_id
        self.player.set_path(path)
        self.feedback(f"Walking to {obj.kind}")

    def update(self) -> None:
        if self.gathering is not None:
            result = self.gathering.update()
            if result is not None:
                self.world_map.apply_resource_states(self.gathering.states)
                self.feedback(result.feedback)

        if self.pending_object_id is None or self.player.is_moving:
            return
        obj = self.world_map.get_object(self.pending_object_id)
        self.pending_object_id = None
        if obj is None:
            return
        if self._in_range(obj.tile):
            self._perform(obj)
        else:
            self.feedback("Too far away")

    def _perform(self, obj: WorldObject) -> None:
        if self._is_gatherable(obj):
            self._perform_gathering(obj)
        elif obj.kind == "bank":
            if self.open_bank is None:
                self.feedback("Bank unavailable")
                return
            self.open_bank()
        elif obj.kind == "shop":
            sold, coins = self.shop.sell_all(self.inventory)
            if sold == 0:
                self.feedback("No sellable items")
                return
            self.add_coins(coins)
            self.feedback(f"Sold {sold} items for {coins} coins")
        else:
            self.feedback("Nothing happens")

    def _perform_gathering(self, obj: WorldObject) -> None:
        if self.gathering is None:
            self.feedback("Nothing happens")
            return
        result = self.gathering.start_gather(
            obj.object_id,
            self.player.tile,
            self.world_map.grid,
            self.world_map.blocked_tiles(),
            allow_movement=False,
        )
        self.world_map.apply_resource_states(self.gathering.states)
        self.feedback(result.feedback)

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

    def _is_gatherable(self, obj: WorldObject) -> bool:
        return self.gathering is not None and obj.object_id in self.gathering.nodes

    def _cancel_gathering(self) -> None:
        if self.gathering is not None:
            self.gathering.cancel_pending()
