from __future__ import annotations

from typing import Any

from panda3d.core import NodePath

from game import settings
from game.systems.gathering import ResourceNode, ResourceNodeState, resource_nodes_from_data
from game.world.grid import Tile, TileGrid
from game.world.objects import WorldObject, make_box, make_cone, make_cylinder, make_grid_lines, make_quad

GRASS = (0.28, 0.58, 0.27, 1.0)
DIRT = (0.48, 0.34, 0.18, 1.0)
WATER = (0.10, 0.38, 0.72, 1.0)
BLOCKED = (0.42, 0.42, 0.45, 1.0)
TRUNK = (0.42, 0.22, 0.10, 1.0)
LEAVES = (0.10, 0.38, 0.16, 1.0)
STUMP = (0.50, 0.28, 0.12, 1.0)
ROCK = (0.44, 0.45, 0.48, 1.0)
DEPLETED_ROCK = (0.25, 0.25, 0.27, 1.0)
FISHING_MARKER = (0.92, 0.92, 0.75, 1.0)
QUIET_WATER = (0.05, 0.22, 0.45, 1.0)
SHOP = (0.78, 0.64, 0.22, 1.0)
NPC = (0.20, 0.34, 0.85, 1.0)


class WorldMap:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.grid = TileGrid(int(data["width"]), int(data["height"]))
        self.dirt_tiles = {_tile(tile) for tile in data.get("dirt_tiles", [])}
        self.water_tiles = {_tile(tile) for tile in data.get("water_tiles", [])}
        self.static_blocked = {_tile(tile) for tile in data.get("blocked_tiles", [])}
        self.resource_nodes = resource_nodes_from_data(data.get("resource_nodes", []))
        self.resource_states: dict[str, ResourceNodeState] = {}
        self.objects: dict[str, WorldObject] = {}
        self.objects_by_tile: dict[Tile, WorldObject] = {}
        self.root: NodePath | None = None

        for resource_node in self.resource_nodes.values():
            obj = WorldObject(
                resource_node.node_id,
                resource_node.node_type,
                resource_node.position,
                blocking=resource_node.blocks_movement,
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
            obj = WorldObject(shop["id"], "shop", _tile(shop["tile"]), blocking=True)
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
            and self.resource_nodes[node_id].node_type == "tree"
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
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile = (x, y)
                if tile in self.water_tiles:
                    color = WATER
                elif tile in self.dirt_tiles:
                    color = DIRT
                else:
                    color = GRASS
                node = make_quad(f"tile_{x}_{y}", settings.TILE_SIZE, color)
                node.reparentTo(self.root)
                node.setPos(x, y, 0)

        grid_node = make_grid_lines(self.grid.width, self.grid.height, (0.05, 0.08, 0.05, 1.0))
        grid_node.reparentTo(self.root)

        for tile in self.static_blocked:
            self._add_obstacle(tile)

        for obj in self.objects.values():
            self._render_object(obj)

    def blocked_tiles(self) -> set[Tile]:
        blocked = set(self.static_blocked)
        for obj in self.objects.values():
            if obj.blocking:
                blocked.add(obj.tile)
        return blocked

    def object_at(self, tile: Tile) -> WorldObject | None:
        return self.objects_by_tile.get(tile)

    def get_object(self, object_id: str) -> WorldObject | None:
        return self.objects.get(object_id)

    def resource_node_for_object(self, obj: WorldObject) -> ResourceNode | None:
        return self.resource_nodes.get(obj.object_id)

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
        if node is None or node.node_type != "tree":
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
        obj.chopped = state.depleted and node.node_type == "tree"
        obj.kind = node.depleted_state if state.depleted else node.node_type
        obj.blocking = False if state.depleted else node.blocks_movement

    def _add_obstacle(self, tile: Tile) -> None:
        if self.root is None:
            return
        x, y = self.grid.to_world(tile)
        node = make_box(f"blocked_{tile[0]}_{tile[1]}", (0.75, 0.75, 0.45), BLOCKED)
        node.reparentTo(self.root)
        node.setPos(x, y, 0)

    def _render_object(self, obj: WorldObject) -> None:
        if self.root is None:
            return

        if obj.node is not None:
            obj.node.removeNode()

        holder = self.root.attachNewNode(obj.object_id)
        x, y = self.grid.to_world(obj.tile)
        holder.setPos(x, y, 0)

        resource_node = self.resource_nodes.get(obj.object_id)
        render_kind = obj.kind
        if resource_node is not None and self.resource_states.get(obj.object_id, ResourceNodeState()).depleted:
            render_kind = resource_node.depleted_state

        if render_kind == "tree":
            trunk = make_cylinder(f"{obj.object_id}_trunk", 0.12, 0.85, 8, TRUNK)
            trunk.reparentTo(holder)
            leaves = make_cone(f"{obj.object_id}_leaves", 0.55, 1.2, 8, LEAVES)
            leaves.reparentTo(holder)
            leaves.setZ(0.65)
        elif render_kind == "stump":
            stump = make_cylinder(f"{obj.object_id}_stump", 0.18, 0.25, 8, STUMP)
            stump.reparentTo(holder)
        elif render_kind == "copper_rock":
            rock = make_box(f"{obj.object_id}_rock", (0.8, 0.75, 0.55), ROCK)
            rock.reparentTo(holder)
            cap = make_cone(f"{obj.object_id}_cap", 0.42, 0.35, 5, ROCK)
            cap.reparentTo(holder)
            cap.setZ(0.45)
        elif render_kind == "depleted_rock":
            rock = make_box(f"{obj.object_id}_depleted_rock", (0.72, 0.68, 0.35), DEPLETED_ROCK)
            rock.reparentTo(holder)
        elif render_kind == "fishing_spot":
            marker = make_cylinder(f"{obj.object_id}_marker", 0.16, 0.08, 10, FISHING_MARKER)
            marker.reparentTo(holder)
            marker.setZ(0.04)
        elif render_kind == "quiet_water":
            marker = make_cylinder(f"{obj.object_id}_quiet", 0.12, 0.04, 10, QUIET_WATER)
            marker.reparentTo(holder)
            marker.setZ(0.04)
        elif render_kind == "shop":
            counter = make_box(f"{obj.object_id}_counter", (0.75, 0.75, 0.45), SHOP)
            counter.reparentTo(holder)
            npc = make_cylinder(f"{obj.object_id}_npc", 0.18, 0.8, 10, NPC)
            npc.reparentTo(holder)
            npc.setPos(0.0, -0.35, 0.0)
            head = make_cone(f"{obj.object_id}_npc_head", 0.22, 0.35, 10, NPC)
            head.reparentTo(holder)
            head.setPos(0.0, -0.35, 0.75)

        obj.node = holder

    def _reindex_objects(self) -> None:
        self.objects_by_tile = {obj.tile: obj for obj in self.objects.values()}


def _tile(value: list[int] | tuple[int, int]) -> Tile:
    return int(value[0]), int(value[1])
