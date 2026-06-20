from __future__ import annotations

from typing import Any

from panda3d.core import NodePath

from game import settings
from game.systems.gathering import ResourceNode, ResourceNodeState, resource_nodes_from_data
from game.world.grid import Tile, TileGrid
from game.world.objects import WorldObject, make_box, make_cone, make_cylinder, make_quad

GRASS_PALETTE = (
    (0.29, 0.47, 0.20, 1.0),
    (0.33, 0.53, 0.24, 1.0),
    (0.24, 0.42, 0.18, 1.0),
    (0.38, 0.56, 0.25, 1.0),
)
DIRT_PALETTE = (
    (0.46, 0.32, 0.16, 1.0),
    (0.55, 0.39, 0.20, 1.0),
    (0.39, 0.27, 0.14, 1.0),
)
WATER_PALETTE = (
    (0.08, 0.30, 0.50, 1.0),
    (0.10, 0.38, 0.62, 1.0),
    (0.06, 0.25, 0.44, 1.0),
)
BLOCKED = (0.34, 0.34, 0.35, 1.0)
BLOCKED_DARK = (0.22, 0.22, 0.23, 1.0)
TRUNK = (0.36, 0.19, 0.08, 1.0)
TRUNK_DARK = (0.24, 0.12, 0.05, 1.0)
LEAVES_DARK = (0.07, 0.27, 0.12, 1.0)
LEAVES = (0.10, 0.38, 0.15, 1.0)
LEAVES_LIGHT = (0.15, 0.47, 0.20, 1.0)
STUMP = (0.44, 0.25, 0.10, 1.0)
STUMP_TOP = (0.68, 0.47, 0.25, 1.0)
ROCK = (0.45, 0.45, 0.43, 1.0)
ROCK_DARK = (0.29, 0.30, 0.31, 1.0)
COPPER = (0.78, 0.40, 0.18, 1.0)
DEPLETED_ROCK = (0.20, 0.21, 0.22, 1.0)
FISHING_MARKER = (0.93, 0.86, 0.56, 1.0)
FISHING_RIPPLE = (0.65, 0.82, 0.82, 1.0)
QUIET_WATER = (0.04, 0.18, 0.32, 1.0)
SHOP_DARK = (0.36, 0.23, 0.12, 1.0)
SHOP_LIGHT = (0.72, 0.56, 0.28, 1.0)
SHOP_CANOPY = (0.70, 0.22, 0.12, 1.0)
NPC_BODY = (0.24, 0.38, 0.70, 1.0)
NPC_HEAD = (0.82, 0.62, 0.42, 1.0)
BANK_DARK = (0.21, 0.18, 0.14, 1.0)
BANK_WOOD = (0.50, 0.31, 0.14, 1.0)
BANK_TRIM = (0.86, 0.70, 0.34, 1.0)
BANK_CLOTH = (0.18, 0.36, 0.52, 1.0)


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

        bank = data.get("bank")
        if bank:
            obj = WorldObject(bank["id"], "bank", _tile(bank["tile"]), blocking=True)
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
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tile = (x, y)
                if tile in self.water_tiles:
                    color = _palette_color(tile, WATER_PALETTE)
                elif tile in self.dirt_tiles:
                    color = _palette_color(tile, DIRT_PALETTE)
                else:
                    color = _palette_color(tile, GRASS_PALETTE)
                node = make_quad(f"tile_{x}_{y}", settings.TILE_SIZE, color)
                node.reparentTo(self.root)
                node.setPos(x, y, 0)
                if tile in self.water_tiles:
                    node.setZ(-0.035)

        for tile in self.static_blocked:
            self._add_obstacle(tile)

        for obj in self.objects.values():
            self._render_object(obj)

    def blocked_tiles(self) -> set[Tile]:
        blocked = set(self.static_blocked)
        blocked.update(self.water_tiles)
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

    def _add_obstacle(self, tile: Tile) -> None:
        if self.root is None:
            return
        x, y = self.grid.to_world(tile)
        holder = self.root.attachNewNode(f"blocked_{tile[0]}_{tile[1]}")
        holder.setPos(x, y, 0)

        base = make_box(f"blocked_{tile[0]}_{tile[1]}_base", (0.72, 0.68, 0.30), BLOCKED_DARK)
        base.reparentTo(holder)
        base.setH(18)

        crest = make_cone(f"blocked_{tile[0]}_{tile[1]}_crest", 0.40, 0.40, 5, BLOCKED)
        crest.reparentTo(holder)
        crest.setZ(0.24)
        crest.setH(-12)

        chip = make_box(f"blocked_{tile[0]}_{tile[1]}_chip", (0.22, 0.20, 0.12), ROCK)
        chip.reparentTo(holder)
        chip.setPos(0.25, -0.18, 0.02)

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
        resource_tier = 1
        if resource_node is not None:
            resource_tier = resource_node.required_level
            if self.resource_states.get(obj.object_id, ResourceNodeState()).depleted:
                render_kind = resource_node.depleted_state
            elif resource_node.skill_id == "woodcutting":
                render_kind = "tree"
            elif resource_node.skill_id == "mining":
                render_kind = "ore_rock"
            elif resource_node.skill_id == "fishing":
                render_kind = "fishing_spot"

        if render_kind == "tree":
            leaf_dark, leaf, leaf_light = _tree_colors(resource_tier)
            trunk = make_cylinder(f"{obj.object_id}_trunk", 0.12, 0.92, 7, TRUNK)
            trunk.reparentTo(holder)
            trunk_shadow = make_cylinder(f"{obj.object_id}_trunk_shadow", 0.08, 0.94, 7, TRUNK_DARK)
            trunk_shadow.reparentTo(holder)
            trunk_shadow.setPos(-0.05, -0.04, 0.0)

            lower = make_cone(f"{obj.object_id}_leaves_lower", 0.62, 0.75, 7, leaf_dark)
            lower.reparentTo(holder)
            lower.setZ(0.55)
            lower.setH(18)

            middle = make_cone(f"{obj.object_id}_leaves_middle", 0.50, 0.70, 7, leaf)
            middle.reparentTo(holder)
            middle.setZ(0.92)
            middle.setH(-10)

            top = make_cone(f"{obj.object_id}_leaves_top", 0.34, 0.52, 7, leaf_light)
            top.reparentTo(holder)
            top.setZ(1.24)
            top.setH(8)
        elif render_kind == "stump":
            stump = make_cylinder(f"{obj.object_id}_stump", 0.20, 0.24, 8, STUMP)
            stump.reparentTo(holder)
            cut = make_cylinder(f"{obj.object_id}_cut", 0.17, 0.03, 8, STUMP_TOP)
            cut.reparentTo(holder)
            cut.setZ(0.24)
        elif render_kind == "ore_rock":
            rock_dark, rock_light, vein_color = _rock_colors(resource_tier)
            base = make_box(f"{obj.object_id}_rock_base", (0.72, 0.66, 0.36), rock_dark)
            base.reparentTo(holder)
            base.setH(15)

            cap = make_cone(f"{obj.object_id}_cap", 0.47, 0.42, 5, rock_light)
            cap.reparentTo(holder)
            cap.setZ(0.30)
            cap.setH(-8)

            vein = make_box(f"{obj.object_id}_ore_vein", (0.16, 0.22, 0.10), vein_color)
            vein.reparentTo(holder)
            vein.setPos(0.15, -0.18, 0.30)
            vein.setH(30)
        elif render_kind == "depleted_rock":
            rock = make_box(f"{obj.object_id}_depleted_rock", (0.64, 0.56, 0.24), DEPLETED_ROCK)
            rock.reparentTo(holder)
            rock.setH(-18)
        elif render_kind == "fishing_spot":
            marker_color, ripple_color = _fishing_colors(resource_tier)
            ripple = make_cylinder(f"{obj.object_id}_ripple", 0.28, 0.02, 12, ripple_color)
            ripple.reparentTo(holder)
            ripple.setZ(0.02)

            marker = make_cylinder(f"{obj.object_id}_marker", 0.08, 0.16, 8, marker_color)
            marker.reparentTo(holder)
            marker.setZ(0.04)
        elif render_kind == "quiet_water":
            marker = make_cylinder(f"{obj.object_id}_quiet", 0.20, 0.02, 10, QUIET_WATER)
            marker.reparentTo(holder)
            marker.setZ(0.04)
        elif render_kind == "shop":
            counter = make_box(f"{obj.object_id}_counter", (0.85, 0.62, 0.34), SHOP_DARK)
            counter.reparentTo(holder)
            counter.setPos(0.0, 0.06, 0.0)

            counter_top = make_box(f"{obj.object_id}_counter_top", (0.95, 0.72, 0.08), SHOP_LIGHT)
            counter_top.reparentTo(holder)
            counter_top.setPos(0.0, 0.06, 0.34)

            canopy = make_box(f"{obj.object_id}_canopy", (0.95, 0.38, 0.10), SHOP_CANOPY)
            canopy.reparentTo(holder)
            canopy.setPos(0.0, -0.24, 0.92)

            post_left = make_cylinder(f"{obj.object_id}_post_left", 0.04, 0.88, 6, TRUNK)
            post_left.reparentTo(holder)
            post_left.setPos(-0.40, -0.24, 0.04)

            post_right = make_cylinder(f"{obj.object_id}_post_right", 0.04, 0.88, 6, TRUNK)
            post_right.reparentTo(holder)
            post_right.setPos(0.40, -0.24, 0.04)

            npc = make_cylinder(f"{obj.object_id}_npc", 0.16, 0.62, 8, NPC_BODY)
            npc.reparentTo(holder)
            npc.setPos(0.0, -0.35, 0.0)

            head = make_cylinder(f"{obj.object_id}_npc_head", 0.17, 0.18, 8, NPC_HEAD)
            head.reparentTo(holder)
            head.setPos(0.0, -0.35, 0.64)
        elif render_kind == "bank":
            counter = make_box(f"{obj.object_id}_counter", (0.92, 0.72, 0.42), BANK_DARK)
            counter.reparentTo(holder)
            counter.setPos(0.0, 0.06, 0.0)

            chest = make_box(f"{obj.object_id}_chest", (0.64, 0.42, 0.34), BANK_WOOD)
            chest.reparentTo(holder)
            chest.setPos(0.0, 0.02, 0.40)

            trim = make_box(f"{obj.object_id}_trim", (0.70, 0.48, 0.06), BANK_TRIM)
            trim.reparentTo(holder)
            trim.setPos(0.0, 0.02, 0.58)

            cloth = make_box(f"{obj.object_id}_cloth", (0.98, 0.22, 0.08), BANK_CLOTH)
            cloth.reparentTo(holder)
            cloth.setPos(0.0, -0.30, 0.86)

            lock = make_box(f"{obj.object_id}_lock", (0.12, 0.05, 0.14), BANK_TRIM)
            lock.reparentTo(holder)
            lock.setPos(0.0, -0.22, 0.43)

        obj.node = holder

    def _reindex_objects(self) -> None:
        self.objects_by_tile = {obj.tile: obj for obj in self.objects.values()}


def _tile(value: list[int] | tuple[int, int]) -> Tile:
    return int(value[0]), int(value[1])


def _palette_color(tile: Tile, palette: tuple[tuple[float, float, float, float], ...]) -> tuple[float, float, float, float]:
    x, y = tile
    index = (x * 17 + y * 31 + x * y * 7) % len(palette)
    return palette[index]


def _tree_colors(level: int) -> tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]:
    palette = {
        1: (LEAVES_DARK, LEAVES, LEAVES_LIGHT),
        2: ((0.12, 0.32, 0.10, 1.0), (0.20, 0.44, 0.14, 1.0), (0.34, 0.56, 0.20, 1.0)),
        3: ((0.12, 0.34, 0.20, 1.0), (0.20, 0.48, 0.30, 1.0), (0.38, 0.62, 0.42, 1.0)),
        4: ((0.26, 0.34, 0.13, 1.0), (0.43, 0.48, 0.18, 1.0), (0.64, 0.58, 0.24, 1.0)),
        5: ((0.05, 0.22, 0.14, 1.0), (0.08, 0.32, 0.22, 1.0), (0.15, 0.42, 0.31, 1.0)),
    }
    return palette.get(level, palette[1])


def _rock_colors(level: int) -> tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]:
    palette = {
        1: (ROCK_DARK, ROCK, COPPER),
        2: ((0.25, 0.25, 0.27, 1.0), (0.52, 0.51, 0.48, 1.0), (0.76, 0.64, 0.46, 1.0)),
        3: ((0.12, 0.12, 0.13, 1.0), (0.25, 0.25, 0.26, 1.0), (0.07, 0.07, 0.08, 1.0)),
        4: ((0.20, 0.27, 0.29, 1.0), (0.34, 0.48, 0.51, 1.0), (0.18, 0.58, 0.64, 1.0)),
        5: ((0.18, 0.25, 0.20, 1.0), (0.34, 0.44, 0.34, 1.0), (0.28, 0.74, 0.36, 1.0)),
    }
    return palette.get(level, palette[1])


def _fishing_colors(level: int) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
    palette = {
        1: (FISHING_MARKER, FISHING_RIPPLE),
        2: ((0.98, 0.62, 0.35, 1.0), (0.64, 0.82, 0.86, 1.0)),
        3: ((0.94, 0.42, 0.30, 1.0), (0.58, 0.76, 0.86, 1.0)),
        4: ((0.48, 0.26, 0.66, 1.0), (0.56, 0.72, 0.86, 1.0)),
        5: ((0.78, 0.76, 0.82, 1.0), (0.50, 0.66, 0.84, 1.0)),
    }
    return palette.get(level, palette[1])
