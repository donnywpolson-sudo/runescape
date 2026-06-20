from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from panda3d.core import NodePath

from game.systems.combat import DropStack, MobState, mobs_from_data
from game.systems.gathering import ResourceNode, ResourceNodeState, resource_nodes_from_data
from game.world import visuals
from game.world.grid import Tile, TileGrid
from game.world.objects import WorldObject


TERRAIN_CHUNK_SIZE = 16


@dataclass
class Decoration:
    decoration_id: str
    kind: str
    tile: Tile
    rotation: float = 0.0
    blocking: bool = False
    node: NodePath | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Decoration":
        position = data["position"]
        return cls(
            decoration_id=str(data["id"]),
            kind=str(data["kind"]),
            tile=(int(position[0]), int(position[1])),
            rotation=float(data.get("rotation", 0.0)),
            blocking=bool(data.get("blocking", False)),
        )


class WorldMap:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.grid = TileGrid(int(data["width"]), int(data["height"]))
        self.dirt_tiles = {_tile(tile) for tile in data.get("dirt_tiles", [])}
        self.water_tiles = {_tile(tile) for tile in data.get("water_tiles", [])}
        self.static_blocked = {_tile(tile) for tile in data.get("blocked_tiles", [])}
        self.resource_nodes = resource_nodes_from_data(data.get("resource_nodes", []))
        self.resource_states: dict[str, ResourceNodeState] = {}
        self.mob_definitions = mobs_from_data(data.get("mobs", []) or [])
        self.mob_states: dict[str, MobState] = {}
        self.ground_item_counter = 0
        self.objects: dict[str, WorldObject] = {}
        self.objects_by_tile: dict[Tile, WorldObject] = {}
        self.shop_stock = [
            dict(raw_stock_item)
            for raw_stock_item in (data.get("shop", {}) or {}).get("stock", []) or []
            if isinstance(raw_stock_item, dict)
        ]
        self.decorations = [
            Decoration.from_dict(raw_decoration)
            for raw_decoration in data.get("decorations", []) or []
            if isinstance(raw_decoration, dict)
        ]
        self.root: NodePath | None = None
        self.terrain_chunks: list[NodePath] = []

        for resource_node in self.resource_nodes.values():
            obj = WorldObject(
                resource_node.node_id,
                resource_node.node_type,
                resource_node.position,
                blocking=resource_node.blocks_movement,
                display_name=resource_node.display_name,
                node_type=resource_node.node_type,
                skill_id=resource_node.skill_id,
                required_level=resource_node.required_level,
                xp_reward=resource_node.xp_reward,
                item_reward=resource_node.item_reward,
                quantity_reward=resource_node.quantity_reward,
                depleted_state=resource_node.depleted_state,
                respawn_seconds=resource_node.respawn_seconds,
            )
            self.objects[obj.object_id] = obj

        shop = data.get("shop")
        if shop:
            obj = WorldObject(shop["id"], "shop", _tile(shop["tile"]), blocking=True, display_name=str(shop.get("name") or "Shop"))
            self.objects[obj.object_id] = obj

        bank = data.get("bank")
        if bank:
            obj = WorldObject(bank["id"], "bank", _tile(bank["tile"]), blocking=True, display_name=str(bank.get("name") or "Bank"))
            self.objects[obj.object_id] = obj

        cooking_range = data.get("cooking_range")
        if cooking_range:
            obj = WorldObject(
                cooking_range["id"],
                "cooking_range",
                _tile(cooking_range["tile"]),
                blocking=True,
                display_name=str(cooking_range.get("name") or "Cooking range"),
            )
            self.objects[obj.object_id] = obj

        combat_dummy = data.get("combat_dummy")
        if combat_dummy:
            obj = WorldObject(
                combat_dummy["id"],
                "combat_dummy",
                _tile(combat_dummy["tile"]),
                blocking=True,
                display_name=str(combat_dummy.get("name") or "Training dummy"),
            )
            self.objects[obj.object_id] = obj

        furnace = data.get("furnace")
        if furnace:
            obj = WorldObject(
                furnace["id"],
                "furnace",
                _tile(furnace["tile"]),
                blocking=True,
                display_name=str(furnace.get("name") or "Furnace"),
            )
            self.objects[obj.object_id] = obj

        anvil = data.get("anvil")
        if anvil:
            obj = WorldObject(
                anvil["id"],
                "anvil",
                _tile(anvil["tile"]),
                blocking=True,
                display_name=str(anvil.get("name") or "Anvil"),
            )
            self.objects[obj.object_id] = obj

        for raw_npc in data.get("npcs", []) or []:
            if not isinstance(raw_npc, dict):
                continue
            obj = WorldObject(
                str(raw_npc["id"]),
                "npc",
                _tile(raw_npc["tile"]),
                blocking=True,
                display_name=str(raw_npc.get("name") or "Villager"),
                quest_id=str(raw_npc.get("quest_id") or ""),
            )
            self.objects[obj.object_id] = obj

        for mob in self.mob_definitions.values():
            obj = WorldObject(
                mob.mob_id,
                "mob",
                mob.position,
                blocking=True,
                display_name=mob.display_name,
                level=mob.level,
                hitpoints=mob.hitpoints,
            )
            self.objects[obj.object_id] = obj

        self._reindex_objects()

    @property
    def player_start(self) -> Tile:
        return _tile(self.data.get("player_start", [15, 15]))

    @property
    def camera_start(self) -> dict[str, float]:
        return dict(self.data.get("camera", {}))

    @property
    def chopped_tree_ids(self) -> set[str]:
        return {
            node_id
            for node_id, state in self.resource_states.items()
            if state.depleted and self.resource_nodes.get(node_id, None)
            and self.resource_nodes[node_id].skill_id == "woodcutting"
        }

    @property
    def depleted_resource_ids(self) -> set[str]:
        return {
            node_id
            for node_id, state in self.resource_states.items()
            if state.depleted and node_id in self.resource_nodes
        }

    def render(self, parent: NodePath) -> None:
        if self.root is not None:
            self.root.removeNode()

        self.root = parent.attachNewNode("world")
        self.terrain_chunks = []
        self._render_terrain_chunks()

        for tile in self.static_blocked:
            self._add_obstacle(tile)

        for decoration in self.decorations:
            self._render_decoration(decoration)

        for obj in self.objects.values():
            self._render_object(obj)

    def blocked_tiles(self) -> set[Tile]:
        blocked = set(self.static_blocked)
        blocked.update(self.water_tiles)
        for obj in self.objects.values():
            if obj.active and obj.blocking:
                blocked.add(obj.tile)
        blocked.update(decoration.tile for decoration in self.decorations if decoration.blocking)
        return blocked

    def object_at(self, tile: Tile) -> WorldObject | None:
        return self.objects_by_tile.get(tile)

    def decoration_at(self, tile: Tile) -> Decoration | None:
        return self.decorations_by_tile.get(tile)

    def get_object(self, object_id: str) -> WorldObject | None:
        return self.objects.get(object_id)

    def resource_node_for_object(self, obj: WorldObject) -> ResourceNode | None:
        return self.resource_nodes.get(obj.object_id)

    def apply_mob_states(self, states: dict[str, MobState]) -> None:
        previous_active = {
            mob_id
            for mob_id in self.mob_definitions
            if self.objects.get(mob_id) is not None and self.objects[mob_id].active
        }
        self.mob_states = {
            mob_id: state for mob_id, state in states.items() if mob_id in self.mob_definitions
        }
        for mob_id in self.mob_definitions:
            self._sync_mob_object(mob_id)
        current_active = {
            mob_id
            for mob_id in self.mob_definitions
            if self.objects.get(mob_id) is not None and self.objects[mob_id].active
        }
        for mob_id in previous_active | current_active:
            obj = self.objects.get(mob_id)
            if obj is not None:
                self._render_object(obj)
        self._reindex_objects()

    def spawn_ground_drops(self, origin: Tile, drops: Iterable[DropStack]) -> list[WorldObject]:
        created: list[WorldObject] = []
        used_tiles: set[Tile] = set()
        for drop in drops:
            if drop.quantity <= 0:
                continue
            tile = self._next_ground_drop_tile(origin, used_tiles)
            if tile is None:
                continue
            used_tiles.add(tile)
            created.append(self.add_ground_item(drop.item_id, drop.quantity, tile))
        return created

    def add_ground_item(
        self,
        item_id: str,
        quantity: int,
        tile: Tile,
        *,
        object_id: str | None = None,
    ) -> WorldObject:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if object_id is None:
            self.ground_item_counter += 1
            object_id = f"ground_item_{self.ground_item_counter:04d}"
        else:
            self._sync_ground_item_counter(object_id)
        obj = WorldObject(
            object_id,
            "ground_item",
            tile,
            blocking=False,
            display_name=item_id.replace("_", " ").title(),
            item_id=item_id,
            quantity=quantity,
        )
        self.objects[obj.object_id] = obj
        self._render_object(obj)
        self._reindex_objects()
        return obj

    def pickup_ground_item(self, object_id: str) -> tuple[str, int] | None:
        obj = self.objects.get(object_id)
        if obj is None or obj.kind != "ground_item":
            return None
        if obj.node is not None:
            obj.node.removeNode()
        self.objects.pop(object_id, None)
        self._reindex_objects()
        return obj.item_id, obj.quantity

    def ground_items_to_dict(self) -> list[dict[str, object]]:
        return [
            {
                "object_id": obj.object_id,
                "item_id": obj.item_id,
                "quantity": obj.quantity,
                "tile": list(obj.tile),
            }
            for obj in sorted(self.objects.values(), key=lambda world_object: world_object.object_id)
            if obj.kind == "ground_item"
        ]

    def load_ground_items(self, data: list[dict[str, Any]]) -> None:
        for object_id, obj in list(self.objects.items()):
            if obj.kind != "ground_item":
                continue
            if obj.node is not None:
                obj.node.removeNode()
            self.objects.pop(object_id, None)
        for raw_item in data:
            if not isinstance(raw_item, dict):
                continue
            raw_tile = raw_item.get("tile")
            if not isinstance(raw_tile, list) or len(raw_tile) != 2:
                continue
            item_id = str(raw_item.get("item_id", ""))
            quantity = int(raw_item.get("quantity", 0))
            object_id = raw_item.get("object_id")
            if not item_id or quantity <= 0:
                continue
            self.add_ground_item(
                item_id,
                quantity,
                (int(raw_tile[0]), int(raw_tile[1])),
                object_id=str(object_id) if object_id else None,
            )
        self._reindex_objects()

    def apply_resource_states(self, states: dict[str, ResourceNodeState]) -> None:
        previous_depleted = {
            node_id for node_id, state in self.resource_states.items() if state.depleted
        }
        self.resource_states = {
            node_id: state for node_id, state in states.items() if node_id in self.resource_nodes
        }
        self._sync_resource_objects()
        current_depleted = {
            node_id for node_id, state in self.resource_states.items() if state.depleted
        }
        if previous_depleted == current_depleted:
            return
        for node_id in previous_depleted | current_depleted:
            obj = self.objects.get(node_id)
            if obj is not None:
                self._render_object(obj)
        self._reindex_objects()

    def set_resource_depleted(self, object_id: str) -> bool:
        if object_id not in self.resource_nodes:
            return False
        current = self.resource_states.get(object_id, ResourceNodeState())
        if current.depleted:
            return False
        self.resource_states[object_id] = ResourceNodeState(depleted=True, respawn_at=None)
        self._sync_resource_object(object_id)
        obj = self.objects.get(object_id)
        if obj is not None:
            self._render_object(obj)
        self._reindex_objects()
        return True

    def set_tree_chopped(self, object_id: str) -> bool:
        node = self.resource_nodes.get(object_id)
        if node is None or node.skill_id != "woodcutting":
            return False
        return self.set_resource_depleted(object_id)

    def load_depleted_resources(self, resource_ids: list[str]) -> None:
        self.resource_states = {
            resource_id: ResourceNodeState(depleted=True, respawn_at=None)
            for resource_id in resource_ids
            if resource_id in self.resource_nodes
        }
        self._sync_resource_objects()
        for object_id in self.resource_states:
            obj = self.objects.get(object_id)
            if obj is not None:
                self._render_object(obj)
        self._reindex_objects()

    def load_chopped_trees(self, chopped_tree_ids: list[str]) -> None:
        self.load_depleted_resources(chopped_tree_ids)

    def reset_chopped_trees(self) -> None:
        self.reset_depleted_resources()

    def reset_depleted_resources(self) -> None:
        affected = list(self.resource_states)
        self.resource_states.clear()
        self._sync_resource_objects()
        for object_id in affected:
            obj = self.objects.get(object_id)
            if obj is not None:
                self._render_object(obj)
        self._reindex_objects()

    def _sync_resource_objects(self) -> None:
        for object_id in self.resource_nodes:
            self._sync_resource_object(object_id)

    def _sync_resource_object(self, object_id: str) -> None:
        node = self.resource_nodes[object_id]
        obj = self.objects.get(object_id)
        if obj is None:
            return
        state = self.resource_states.get(object_id, ResourceNodeState())
        obj.depleted = state.depleted
        obj.chopped = state.depleted and node.skill_id == "woodcutting"
        obj.kind = node.depleted_state if state.depleted else node.node_type
        obj.blocking = False if state.depleted else node.blocks_movement

    def _sync_mob_object(self, mob_id: str) -> None:
        mob = self.mob_definitions[mob_id]
        obj = self.objects.get(mob_id)
        if obj is None:
            return
        state = self.mob_states.get(mob_id, MobState(hitpoints=mob.hitpoints))
        obj.kind = "mob"
        obj.tile = mob.position
        obj.display_name = mob.display_name
        obj.level = mob.level
        obj.hitpoints = state.hitpoints
        obj.active = not state.dead
        obj.blocking = not state.dead

    def _next_ground_drop_tile(self, origin: Tile, used_tiles: set[Tile]) -> Tile | None:
        candidates = [origin]
        candidates.extend(self.grid.neighbors(origin, diagonals=True))
        blocked = self.blocked_tiles()
        occupied = {
            obj.tile
            for obj in self.objects.values()
            if obj.active and obj.kind != "mob"
        }
        for tile in candidates:
            if tile in used_tiles or tile in blocked or tile in occupied:
                continue
            if self.grid.in_bounds(tile):
                return tile
        return None

    def _sync_ground_item_counter(self, object_id: str) -> None:
        prefix = "ground_item_"
        if not object_id.startswith(prefix):
            return
        try:
            value = int(object_id[len(prefix):])
        except ValueError:
            return
        self.ground_item_counter = max(self.ground_item_counter, value)

    def _render_terrain_chunks(self) -> None:
        if self.root is None:
            return
        for chunk_y in range(0, self.grid.height, TERRAIN_CHUNK_SIZE):
            for chunk_x in range(0, self.grid.width, TERRAIN_CHUNK_SIZE):
                chunk = self.root.attachNewNode(
                    f"terrain_chunk_{chunk_x // TERRAIN_CHUNK_SIZE}_{chunk_y // TERRAIN_CHUNK_SIZE}"
                )
                max_y = min(chunk_y + TERRAIN_CHUNK_SIZE, self.grid.height)
                max_x = min(chunk_x + TERRAIN_CHUNK_SIZE, self.grid.width)
                for y in range(chunk_y, max_y):
                    for x in range(chunk_x, max_x):
                        tile = (x, y)
                        terrain = self._terrain_at(tile)
                        visuals.render_terrain_tile(chunk, tile, terrain, self._terrain_edges(tile, terrain))
                chunk.flattenStrong()
                self.terrain_chunks.append(chunk)

    def _add_obstacle(self, tile: Tile) -> None:
        if self.root is None:
            return
        x, y = self.grid.to_world(tile)
        holder = self.root.attachNewNode(f"blocked_{tile[0]}_{tile[1]}")
        holder.setPos(x, y, 0)
        visuals.render_static_obstacle(holder, f"blocked_{tile[0]}_{tile[1]}")

    def _render_object(self, obj: WorldObject) -> None:
        if self.root is None:
            return

        if obj.node is not None:
            obj.node.removeNode()
            obj.node = None

        if not obj.active:
            return

        holder = self.root.attachNewNode(obj.object_id)
        x, y = self.grid.to_world(obj.tile)
        holder.setPos(x, y, 0)
        visuals.render_world_object(
            holder,
            obj,
            self.resource_nodes.get(obj.object_id),
            self.resource_states.get(obj.object_id, ResourceNodeState()),
        )
        obj.node = holder

    def _render_decoration(self, decoration: Decoration) -> None:
        if self.root is None:
            return

        if decoration.node is not None:
            decoration.node.removeNode()

        holder = self.root.attachNewNode(decoration.decoration_id)
        x, y = self.grid.to_world(decoration.tile)
        holder.setPos(x, y, 0)
        holder.setH(decoration.rotation)
        visuals.render_decoration(holder, decoration.decoration_id, decoration.kind)
        decoration.node = holder

    def _reindex_objects(self) -> None:
        self.objects_by_tile = {
            obj.tile: obj
            for obj in self.objects.values()
            if obj.active and obj.is_interactable
        }
        self.decorations_by_tile = {decoration.tile: decoration for decoration in self.decorations}

    def terrain_label(self, tile: Tile) -> str:
        return {
            "dirt": "Dirt path",
            "grass": "Grass",
            "water": "Water",
        }.get(self._terrain_at(tile), "Ground")

    def _terrain_at(self, tile: Tile) -> str:
        if tile in self.water_tiles:
            return "water"
        if tile in self.dirt_tiles:
            return "dirt"
        return "grass"

    def _terrain_edges(self, tile: Tile, terrain: str) -> set[str]:
        edges: set[str] = set()
        for direction, (dx, dy) in visuals.CARDINAL_DIRECTIONS.items():
            neighbor = (tile[0] + dx, tile[1] + dy)
            if not self.grid.in_bounds(neighbor) or self._terrain_at(neighbor) != terrain:
                edges.add(direction)
        return edges


def _tile(value: list[int] | tuple[int, int]) -> Tile:
    return int(value[0]), int(value[1])
