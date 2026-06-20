from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Iterable

from game.world.grid import Tile, TileGrid
from game.world.pathfinding import find_path


TimeProvider = Callable[[], float]


@dataclass(frozen=True)
class ResourceNode:
    node_id: str
    node_type: str
    skill_id: str
    required_level: int
    xp_reward: int
    item_reward: str
    quantity_reward: int
    depleted_state: str
    respawn_seconds: float
    blocks_movement: bool
    position: Tile

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceNode":
        position = data["position"]
        return cls(
            node_id=str(data["node_id"]),
            node_type=str(data["node_type"]),
            skill_id=str(data["skill_id"]),
            required_level=int(data["required_level"]),
            xp_reward=int(data["xp_reward"]),
            item_reward=str(data["item_reward"]),
            quantity_reward=int(data["quantity_reward"]),
            depleted_state=str(data["depleted_state"]),
            respawn_seconds=float(data["respawn_seconds"]),
            blocks_movement=bool(data["blocks_movement"]),
            position=(int(position[0]), int(position[1])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "skill_id": self.skill_id,
            "required_level": self.required_level,
            "xp_reward": self.xp_reward,
            "item_reward": self.item_reward,
            "quantity_reward": self.quantity_reward,
            "depleted_state": self.depleted_state,
            "respawn_seconds": self.respawn_seconds,
            "blocks_movement": self.blocks_movement,
            "position": list(self.position),
        }


@dataclass
class ResourceNodeState:
    depleted: bool = False
    respawn_at: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceNodeState":
        respawn_at = data.get("respawn_at")
        return cls(
            depleted=bool(data.get("depleted", False)),
            respawn_at=float(respawn_at) if respawn_at is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"depleted": self.depleted, "respawn_at": self.respawn_at}


@dataclass(frozen=True)
class GatheringResult:
    success: bool
    feedback: str
    node_id: str | None = None
    skill_id: str | None = None
    item_id: str | None = None
    quantity: int = 0
    xp: int = 0
    new_player_tile: Tile | None = None


class GatheringSystem:
    def __init__(
        self,
        nodes: Iterable[ResourceNode] | dict[str, ResourceNode],
        inventory: Any,
        skills: Any,
        *,
        time_provider: TimeProvider = time.time,
        states: dict[str, ResourceNodeState] | None = None,
    ) -> None:
        self.nodes = dict(nodes) if isinstance(nodes, dict) else {node.node_id: node for node in nodes}
        self.inventory = inventory
        self.skills = skills
        self.time_provider = time_provider
        self.states: dict[str, ResourceNodeState] = states or {}

    def gather(
        self,
        node_id: str,
        player_tile: Tile,
        grid: TileGrid,
        blocked_tiles: Iterable[Tile],
        *,
        allow_movement: bool = True,
    ) -> GatheringResult:
        node = self.nodes.get(node_id)
        if node is None:
            return GatheringResult(False, "No object selected")

        if self.is_depleted(node.node_id):
            return GatheringResult(False, f"{_node_label(node)} is depleted", node_id=node.node_id)

        blocked = set(blocked_tiles)
        destination = self._find_interaction_tile(
            node,
            player_tile,
            grid,
            blocked,
            allow_movement=allow_movement,
        )
        if destination is None:
            return GatheringResult(False, "No path" if allow_movement else "Too far away", node_id=node.node_id)

        current_level = _skill_level(self.skills, node.skill_id)
        if current_level < node.required_level:
            return GatheringResult(
                False,
                f"You need {_skill_name(self.skills, node.skill_id)} level {node.required_level}",
                node_id=node.node_id,
                new_player_tile=destination if destination != player_tile else None,
            )

        self.inventory.add(node.item_reward, node.quantity_reward)
        self.skills.add_xp(node.skill_id, node.xp_reward)
        self._deplete(node)

        return GatheringResult(
            True,
            _success_feedback(node, self.skills),
            node_id=node.node_id,
            skill_id=node.skill_id,
            item_id=node.item_reward,
            quantity=node.quantity_reward,
            xp=node.xp_reward,
            new_player_tile=destination if destination != player_tile else None,
        )

    def is_depleted(self, node_id: str) -> bool:
        self._refresh_node(node_id)
        return self.states.get(node_id, ResourceNodeState()).depleted

    def refresh_all(self) -> None:
        for node_id in list(self.nodes):
            self._refresh_node(node_id)

    def blocking_tiles(self) -> set[Tile]:
        return {
            node.position
            for node in self.nodes.values()
            if node.blocks_movement and not self.is_depleted(node.node_id)
        }

    def to_dict(self) -> dict[str, dict[str, Any]]:
        self.refresh_all()
        return {
            node_id: state.to_dict()
            for node_id, state in sorted(self.states.items())
            if node_id in self.nodes and (state.depleted or state.respawn_at is not None)
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self.states.clear()
        for node_id, raw_state in data.items():
            if node_id not in self.nodes or not isinstance(raw_state, dict):
                continue
            self.states[node_id] = ResourceNodeState.from_dict(raw_state)
        self.refresh_all()

    def reset_node(self, node_id: str) -> None:
        self.states.pop(node_id, None)

    def _deplete(self, node: ResourceNode) -> None:
        respawn_at = None
        if node.respawn_seconds > 0:
            respawn_at = self.time_provider() + node.respawn_seconds
        self.states[node.node_id] = ResourceNodeState(depleted=True, respawn_at=respawn_at)

    def _refresh_node(self, node_id: str) -> None:
        state = self.states.get(node_id)
        if state is None or not state.depleted or state.respawn_at is None:
            return
        if self.time_provider() >= state.respawn_at:
            self.states.pop(node_id, None)

    def _find_interaction_tile(
        self,
        node: ResourceNode,
        player_tile: Tile,
        grid: TileGrid,
        blocked_tiles: set[Tile],
        *,
        allow_movement: bool,
    ) -> Tile | None:
        interaction_tiles = self._interaction_tiles(node, grid, blocked_tiles)
        if player_tile in interaction_tiles:
            return player_tile

        if not allow_movement:
            return None

        reachable: list[tuple[int, Tile]] = []
        for tile in interaction_tiles:
            path = find_path(grid, player_tile, tile, blocked_tiles)
            if path:
                reachable.append((len(path), tile))

        if not reachable:
            return None
        reachable.sort()
        return reachable[0][1]

    def _interaction_tiles(
        self,
        node: ResourceNode,
        grid: TileGrid,
        blocked_tiles: set[Tile],
    ) -> list[Tile]:
        tiles: list[Tile] = []
        if not node.blocks_movement and grid.in_bounds(node.position) and node.position not in blocked_tiles:
            tiles.append(node.position)

        x, y = node.position
        for tile in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if grid.in_bounds(tile) and tile not in blocked_tiles:
                tiles.append(tile)
        return tiles


def resource_nodes_from_data(data: Iterable[dict[str, Any]]) -> dict[str, ResourceNode]:
    nodes = [ResourceNode.from_dict(raw_node) for raw_node in data]
    return {node.node_id: node for node in nodes}


def _skill_level(skills: Any, skill_id: str) -> int:
    if hasattr(skills, "level"):
        return int(skills.level(skill_id))
    return int(skills.get(skill_id).level)


def _skill_name(skills: Any, skill_id: str) -> str:
    if hasattr(skills, "display_name"):
        return str(skills.display_name(skill_id))
    definition = getattr(skills, "definitions", {}).get(skill_id, {})
    return str(definition.get("display_name") or definition.get("name") or skill_id.replace("_", " ").title())


def _item_name(item_id: str) -> str:
    return item_id.replace("_", " ")


def _node_label(node: ResourceNode) -> str:
    labels = {
        "tree": "Tree",
        "copper_rock": "Copper rock",
        "fishing_spot": "Fishing spot",
    }
    return labels.get(node.node_type, node.node_type.replace("_", " ").title())


def _success_feedback(node: ResourceNode, skills: Any) -> str:
    prefix = {
        "tree": "Chopped tree",
        "copper_rock": "Mined copper",
        "fishing_spot": "Caught fish",
    }.get(node.node_type, f"Gathered {_node_label(node).lower()}")
    return (
        f"{prefix}: +{node.quantity_reward} {_item_name(node.item_reward)}, "
        f"+{node.xp_reward} {_skill_name(skills, node.skill_id)} XP"
    )
