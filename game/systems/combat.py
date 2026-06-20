from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Iterable

from game import settings
from game.world.grid import Tile, TileGrid


TimeProvider = Callable[[], float]


@dataclass(frozen=True)
class DropStack:
    item_id: str
    quantity: int

    def to_dict(self) -> dict[str, object]:
        return {"item_id": self.item_id, "quantity": self.quantity}


@dataclass(frozen=True)
class MobDefinition:
    mob_id: str
    display_name: str
    level: int
    hitpoints: int
    attack_seconds: float
    respawn_seconds: float
    position: Tile
    drops: tuple[DropStack, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MobDefinition":
        position = data["position"]
        raw_display_name = data.get("display_name")
        display_name = (
            str(raw_display_name)
            if isinstance(raw_display_name, str) and raw_display_name
            else str(data["mob_id"]).replace("_", " ").title()
        )
        return cls(
            mob_id=str(data["mob_id"]),
            display_name=display_name,
            level=int(data["level"]),
            hitpoints=int(data["hitpoints"]),
            attack_seconds=float(data["attack_seconds"]),
            respawn_seconds=float(data["respawn_seconds"]),
            position=(int(position[0]), int(position[1])),
            drops=tuple(
                DropStack(str(drop["item_id"]), int(drop.get("quantity", 1)))
                for drop in data.get("drops", [])
                if isinstance(drop, dict)
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "mob_id": self.mob_id,
            "display_name": self.display_name,
            "level": self.level,
            "hitpoints": self.hitpoints,
            "attack_seconds": self.attack_seconds,
            "respawn_seconds": self.respawn_seconds,
            "position": list(self.position),
            "drops": [drop.to_dict() for drop in self.drops],
        }


@dataclass
class MobState:
    hitpoints: int
    dead: bool = False
    respawn_at: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], max_hitpoints: int) -> "MobState":
        raw_hitpoints = data.get("hitpoints", max_hitpoints)
        try:
            hitpoints = int(raw_hitpoints)
        except (TypeError, ValueError):
            hitpoints = max_hitpoints
        return cls(
            hitpoints=max(0, min(max_hitpoints, hitpoints)),
            dead=bool(data.get("dead", False)),
            respawn_at=float(data["respawn_at"]) if data.get("respawn_at") is not None else None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "hitpoints": self.hitpoints,
            "dead": self.dead,
            "respawn_at": self.respawn_at,
        }


@dataclass(frozen=True)
class PendingCombat:
    mob_id: str
    complete_at: float
    duration: float


@dataclass(frozen=True)
class CombatResult:
    success: bool
    feedback: str
    mob_id: str | None = None
    pending: bool = False
    duration: float = 0.0
    killed: bool = False
    drops: tuple[DropStack, ...] = ()
    player_damage: int = 0
    enemy_damage: int = 0
    player_dead: bool = False


class CombatSystem:
    def __init__(
        self,
        mobs: Iterable[MobDefinition] | dict[str, MobDefinition],
        *,
        time_provider: TimeProvider = time.time,
        damage_per_hit: int = 1,
        skills: Any | None = None,
        current_hitpoints: int | None = None,
    ) -> None:
        self.mobs = dict(mobs) if isinstance(mobs, dict) else {mob.mob_id: mob for mob in mobs}
        self.time_provider = time_provider
        self.damage_per_hit = max(1, int(damage_per_hit))
        self.defence_bonus = 0
        self.skills = skills
        self.current_hitpoints = int(current_hitpoints) if current_hitpoints is not None else self.max_hitpoints()
        self.states: dict[str, MobState] = {}
        self.pending: PendingCombat | None = None

    def max_hitpoints(self) -> int:
        if self.skills is None:
            return 10
        if hasattr(self.skills, "level"):
            return max(1, int(self.skills.level("hitpoints")))
        return max(1, int(self.skills.get("hitpoints").level))

    def heal(self, amount: int) -> int:
        if amount <= 0:
            return 0
        before = self.current_hitpoints
        self.current_hitpoints = min(self.max_hitpoints(), self.current_hitpoints + amount)
        return self.current_hitpoints - before

    def load_player_hitpoints(self, value: object | None) -> None:
        try:
            hitpoints = int(value) if value is not None else self.max_hitpoints()
        except (TypeError, ValueError):
            hitpoints = self.max_hitpoints()
        self.current_hitpoints = max(1, min(self.max_hitpoints(), hitpoints))

    def reset_player(self) -> None:
        self.current_hitpoints = self.max_hitpoints()
        self.cancel_pending()

    def start_attack(
        self,
        mob_id: str,
        player_tile: Tile,
        grid: TileGrid,
        _blocked_tiles: Iterable[Tile],
    ) -> CombatResult:
        mob = self.mobs.get(mob_id)
        if mob is None:
            return CombatResult(False, "No mob selected")
        if not self._is_adjacent(player_tile, mob.position) or not grid.in_bounds(player_tile):
            return CombatResult(False, "Too far away", mob_id=mob.mob_id)
        if self.is_dead(mob.mob_id):
            return CombatResult(False, f"{mob.display_name} is defeated", mob_id=mob.mob_id)
        if self.current_hitpoints <= 0:
            return CombatResult(False, "You need to recover before fighting", mob_id=mob.mob_id, player_dead=True)

        if self.pending is not None:
            if self.pending.mob_id == mob.mob_id:
                return CombatResult(
                    True,
                    _pending_feedback(mob, self.remaining_seconds()),
                    mob_id=mob.mob_id,
                    pending=True,
                    duration=self.pending.duration,
                )
            self.cancel_pending()

        self.pending = PendingCombat(
            mob_id=mob.mob_id,
            complete_at=self.time_provider() + mob.attack_seconds,
            duration=mob.attack_seconds,
        )
        return CombatResult(
            True,
            f"Attacking {mob.display_name}... {mob.attack_seconds:.1f}s",
            mob_id=mob.mob_id,
            pending=True,
            duration=mob.attack_seconds,
        )

    def update(self) -> CombatResult | None:
        if self.pending is None or self.time_provider() < self.pending.complete_at:
            return None

        pending = self.pending
        self.pending = None
        mob = self.mobs.get(pending.mob_id)
        if mob is None:
            return CombatResult(False, "No mob selected")
        if self.is_dead(mob.mob_id):
            return CombatResult(False, f"{mob.display_name} is defeated", mob_id=mob.mob_id)

        state = self._state_for(mob)
        player_damage = self._player_damage()
        remaining_hitpoints = max(0, state.hitpoints - player_damage)
        self._grant_combat_xp(player_damage)
        if remaining_hitpoints <= 0:
            self.states[mob.mob_id] = MobState(
                hitpoints=0,
                dead=True,
                respawn_at=self.time_provider() + mob.respawn_seconds if mob.respawn_seconds > 0 else None,
            )
            return CombatResult(
                True,
                f"Defeated {mob.display_name}",
                mob_id=mob.mob_id,
                killed=True,
                drops=mob.drops,
                player_damage=player_damage,
            )

        enemy_damage = self._enemy_damage(mob)
        self.current_hitpoints = max(0, self.current_hitpoints - enemy_damage)
        if self.current_hitpoints <= 0:
            self.states[mob.mob_id] = MobState(hitpoints=remaining_hitpoints)
            return CombatResult(
                False,
                f"You were defeated by {mob.display_name}",
                mob_id=mob.mob_id,
                player_damage=player_damage,
                enemy_damage=enemy_damage,
                player_dead=True,
            )

        self.states[mob.mob_id] = MobState(hitpoints=remaining_hitpoints)
        self.pending = PendingCombat(
            mob_id=mob.mob_id,
            complete_at=self.time_provider() + mob.attack_seconds,
            duration=mob.attack_seconds,
        )
        return CombatResult(
            True,
            f"Hit {mob.display_name}: {remaining_hitpoints} HP left; {mob.display_name} hit you for {enemy_damage}",
            mob_id=mob.mob_id,
            pending=True,
            duration=mob.attack_seconds,
            player_damage=player_damage,
            enemy_damage=enemy_damage,
        )

    def cancel_pending(self) -> bool:
        if self.pending is None:
            return False
        self.pending = None
        return True

    def remaining_seconds(self) -> float:
        if self.pending is None:
            return 0.0
        return max(0.0, self.pending.complete_at - self.time_provider())

    def refresh_all(self) -> None:
        for mob_id in list(self.states):
            self._refresh_mob(mob_id)

    def is_dead(self, mob_id: str) -> bool:
        self._refresh_mob(mob_id)
        return self.states.get(mob_id, self._default_state(mob_id)).dead

    def to_dict(self) -> dict[str, dict[str, object]]:
        self.refresh_all()
        return {
            mob_id: state.to_dict()
            for mob_id, state in sorted(self.states.items())
            if mob_id in self.mobs and not self._is_default_state(mob_id, state)
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self.cancel_pending()
        self.states.clear()
        for mob_id, raw_state in data.items():
            mob = self.mobs.get(str(mob_id))
            if mob is None or not isinstance(raw_state, dict):
                continue
            self.states[mob.mob_id] = MobState.from_dict(raw_state, mob.hitpoints)
        self.refresh_all()

    def _state_for(self, mob: MobDefinition) -> MobState:
        self._refresh_mob(mob.mob_id)
        return self.states.get(mob.mob_id, MobState(hitpoints=mob.hitpoints))

    def _default_state(self, mob_id: str) -> MobState:
        mob = self.mobs.get(mob_id)
        return MobState(hitpoints=mob.hitpoints if mob is not None else 0)

    def _is_default_state(self, mob_id: str, state: MobState) -> bool:
        mob = self.mobs[mob_id]
        return state.hitpoints == mob.hitpoints and not state.dead and state.respawn_at is None

    def _refresh_mob(self, mob_id: str) -> None:
        mob = self.mobs.get(mob_id)
        state = self.states.get(mob_id)
        if mob is None or state is None or not state.dead or state.respawn_at is None:
            return
        if self.time_provider() >= state.respawn_at:
            self.states.pop(mob_id, None)
            if self.pending is not None and self.pending.mob_id == mob_id:
                self.cancel_pending()

    def _is_adjacent(self, player_tile: Tile, target_tile: Tile) -> bool:
        distance = max(abs(player_tile[0] - target_tile[0]), abs(player_tile[1] - target_tile[1]))
        return 0 < distance <= settings.INTERACTION_RANGE

    def _player_damage(self) -> int:
        strength_bonus = 0
        if self.skills is not None and hasattr(self.skills, "level"):
            strength_bonus = max(0, int(self.skills.level("strength")) - 1) // 10
        return max(1, self.damage_per_hit + strength_bonus)

    def _enemy_damage(self, mob: MobDefinition) -> int:
        return max(0, max(1, mob.level // 3) - self.defence_bonus)

    def _grant_combat_xp(self, damage: int) -> None:
        if self.skills is None or damage <= 0 or not hasattr(self.skills, "add_xp"):
            return
        self.skills.add_xp("attack", damage * 4)
        self.skills.add_xp("strength", damage * 4)
        self.skills.add_xp("defence", damage * 2)
        self.skills.add_xp("hitpoints", damage)


def mobs_from_data(data: Iterable[dict[str, Any]]) -> dict[str, MobDefinition]:
    mobs = [MobDefinition.from_dict(raw_mob) for raw_mob in data]
    return {mob.mob_id: mob for mob in mobs}


def _pending_feedback(mob: MobDefinition, remaining_seconds: float) -> str:
    return f"Attacking {mob.display_name}... {remaining_seconds:.1f}s"
