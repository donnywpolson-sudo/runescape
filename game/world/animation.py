from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable


Vec3Tuple = tuple[float, float, float]
Vec4Tuple = tuple[float, float, float, float]


@dataclass(frozen=True)
class _NodeState:
    pos: Vec3Tuple
    hpr: Vec3Tuple
    scale: Vec3Tuple
    color_scale: Vec4Tuple


@dataclass
class _Track:
    key: str
    node: Any
    base: _NodeState
    apply: Callable[["_Track"], None]
    duration: float | None = None
    elapsed: float = 0.0
    reset_pos: bool = False
    reset_hpr: bool = False
    reset_scale: bool = False
    reset_color: bool = False
    restore_on_finish: bool = True
    cleanup: Callable[[], None] | None = None


class SceneAnimator:
    def __init__(self) -> None:
        self._tracks: dict[str, _Track] = {}

    def update(self, dt: float) -> None:
        if dt <= 0:
            return
        finished: list[str] = []
        for key, track in list(self._tracks.items()):
            if not _node_is_live(track.node):
                finished.append(key)
                continue
            track.elapsed += dt
            track.apply(track)
            if track.duration is not None and track.elapsed >= track.duration:
                finished.append(key)

        for key in finished:
            self._finish(key)

    def stop(self, key: str) -> bool:
        track = self._tracks.pop(key, None)
        if track is None:
            return False
        self._restore(track)
        if track.cleanup is not None:
            track.cleanup()
        return True

    def stop_prefix(self, prefix: str) -> int:
        keys = [key for key in self._tracks if key.startswith(prefix)]
        for key in keys:
            self.stop(key)
        return len(keys)

    def stop_all(self) -> None:
        for key in list(self._tracks):
            self.stop(key)

    def active_keys(self) -> set[str]:
        return set(self._tracks)

    def start_bob(self, key: str, node: Any, *, amplitude: float = 0.05, speed: float = 7.0) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            z = track.base.pos[2] + math.sin(track.elapsed * speed) * amplitude
            _set_pos(track.node, (track.base.pos[0], track.base.pos[1], z))

        self._replace(_Track(key, node, base, apply, reset_pos=True))

    def start_pulse(self, key: str, node: Any, *, amplitude: float = 0.08, speed: float = 6.0) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            factor = 1.0 + math.sin(track.elapsed * speed) * amplitude
            _set_scale(
                track.node,
                (
                    track.base.scale[0] * factor,
                    track.base.scale[1] * factor,
                    track.base.scale[2] * factor,
                ),
            )

        self._replace(_Track(key, node, base, apply, reset_scale=True))

    def start_shake(self, key: str, node: Any, *, amplitude: float = 0.04, speed: float = 14.0) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            x = track.base.pos[0] + math.sin(track.elapsed * speed) * amplitude
            y = track.base.pos[1] + math.cos(track.elapsed * speed * 0.7) * amplitude * 0.55
            _set_pos(track.node, (x, y, track.base.pos[2]))

        self._replace(_Track(key, node, base, apply, reset_pos=True))

    def start_tilt(
        self,
        key: str,
        node: Any,
        *,
        pitch: float = 0.0,
        roll: float = 5.0,
        speed: float = 6.0,
    ) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            offset = math.sin(track.elapsed * speed)
            _set_hpr(
                track.node,
                (
                    track.base.hpr[0],
                    track.base.hpr[1] + pitch * offset,
                    track.base.hpr[2] + roll * offset,
                ),
            )

        self._replace(_Track(key, node, base, apply, reset_hpr=True))

    def start_rotate(self, key: str, node: Any, *, degrees_per_second: float = 45.0) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            _set_hpr(
                track.node,
                (
                    track.base.hpr[0] + track.elapsed * degrees_per_second,
                    track.base.hpr[1],
                    track.base.hpr[2],
                ),
            )

        self._replace(_Track(key, node, base, apply, reset_hpr=True))

    def start_swing(
        self,
        key: str,
        node: Any,
        *,
        axis: str = "p",
        amplitude: float = 35.0,
        speed: float = 8.0,
        phase: float = 0.0,
    ) -> None:
        base = _capture(node)
        axis_index = {"h": 0, "p": 1, "r": 2}.get(axis.lower(), 1)

        def apply(track: _Track) -> None:
            hpr = list(track.base.hpr)
            hpr[axis_index] += math.sin(track.elapsed * speed + phase) * amplitude
            _set_hpr(track.node, (hpr[0], hpr[1], hpr[2]))

        self._replace(_Track(key, node, base, apply, reset_hpr=True))

    def start_flash(
        self,
        key: str,
        node: Any,
        *,
        color: Vec4Tuple = (1.35, 1.18, 0.70, 1.0),
        speed: float = 7.0,
    ) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            factor = (math.sin(track.elapsed * speed) + 1.0) * 0.5
            _set_color(track.node, _lerp4(track.base.color_scale, color, factor))

        self._replace(_Track(key, node, base, apply, reset_color=True))

    def start_recoil(
        self,
        key: str,
        node: Any,
        *,
        direction: Vec3Tuple = (0.0, -1.0, 0.0),
        distance: float = 0.10,
        duration: float = 0.22,
    ) -> None:
        base = _capture(node)
        direction = _normalize(direction)

        def apply(track: _Track) -> None:
            progress = _progress(track)
            offset = math.sin(math.pi * progress) * distance
            _set_pos(
                track.node,
                (
                    track.base.pos[0] + direction[0] * offset,
                    track.base.pos[1] + direction[1] * offset,
                    track.base.pos[2] + direction[2] * offset,
                ),
            )

        self._replace(_Track(key, node, base, apply, duration=duration, reset_pos=True))

    def start_hit(
        self,
        key: str,
        node: Any,
        *,
        direction: Vec3Tuple = (0.0, -1.0, 0.0),
        distance: float = 0.08,
        duration: float = 0.24,
    ) -> None:
        base = _capture(node)
        direction = _normalize(direction)

        def apply(track: _Track) -> None:
            progress = _progress(track)
            pulse = math.sin(math.pi * progress)
            _set_pos(
                track.node,
                (
                    track.base.pos[0] + direction[0] * pulse * distance,
                    track.base.pos[1] + direction[1] * pulse * distance,
                    track.base.pos[2] + direction[2] * pulse * distance,
                ),
            )
            _set_color(track.node, _lerp4(track.base.color_scale, (1.45, 0.78, 0.58, 1.0), pulse))

        self._replace(
            _Track(
                key,
                node,
                base,
                apply,
                duration=duration,
                reset_pos=True,
                reset_color=True,
            )
        )

    def start_defeat(self, key: str, node: Any, *, duration: float = 0.55) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            progress = _progress(track)
            eased = progress * progress * (3.0 - 2.0 * progress)
            _set_pos(
                track.node,
                (
                    track.base.pos[0],
                    track.base.pos[1],
                    track.base.pos[2] - 0.32 * eased,
                ),
            )
            _set_hpr(
                track.node,
                (
                    track.base.hpr[0],
                    track.base.hpr[1] + 72.0 * eased,
                    track.base.hpr[2] + 18.0 * eased,
                ),
            )
            scale = max(0.15, 1.0 - 0.45 * eased)
            _set_scale(
                track.node,
                (
                    track.base.scale[0] * scale,
                    track.base.scale[1] * scale,
                    track.base.scale[2] * scale,
                ),
            )
            _set_color(track.node, _lerp4(track.base.color_scale, (0.75, 0.58, 0.45, 0.70), eased))

        self._replace(
            _Track(
                key,
                node,
                base,
                apply,
                duration=duration,
                reset_pos=True,
                reset_hpr=True,
                reset_scale=True,
                reset_color=True,
                restore_on_finish=False,
                cleanup=lambda: node.removeNode() if hasattr(node, "removeNode") else None,
            )
        )

    def start_pop_in(self, key: str, node: Any, *, duration: float = 0.28) -> None:
        base = _capture(node)

        def apply(track: _Track) -> None:
            progress = _progress(track)
            bounce = math.sin(math.pi * progress) * 0.14
            scale = 0.35 + progress * 0.65 + bounce
            _set_scale(
                track.node,
                (
                    track.base.scale[0] * scale,
                    track.base.scale[1] * scale,
                    track.base.scale[2] * scale,
                ),
            )
            _set_pos(
                track.node,
                (
                    track.base.pos[0],
                    track.base.pos[1],
                    track.base.pos[2] + math.sin(math.pi * progress) * 0.10,
                ),
            )

        self._replace(
            _Track(
                key,
                node,
                base,
                apply,
                duration=duration,
                reset_pos=True,
                reset_scale=True,
            )
        )

    def _replace(self, track: _Track) -> None:
        if track.key in self._tracks:
            self.stop(track.key)
        self._tracks[track.key] = track

    def _finish(self, key: str) -> None:
        track = self._tracks.pop(key, None)
        if track is None:
            return
        if track.restore_on_finish:
            self._restore(track)
        if track.cleanup is not None:
            track.cleanup()

    def _restore(self, track: _Track) -> None:
        if not _node_is_live(track.node):
            return
        if track.reset_pos:
            _set_pos(track.node, track.base.pos)
        if track.reset_hpr:
            _set_hpr(track.node, track.base.hpr)
        if track.reset_scale:
            _set_scale(track.node, track.base.scale)
        if track.reset_color:
            _set_color(track.node, track.base.color_scale)


def _capture(node: Any) -> _NodeState:
    return _NodeState(
        pos=_vec3_from_call(node, "getPos", (0.0, 0.0, 0.0)),
        hpr=_vec3_from_call(node, "getHpr", (0.0, 0.0, 0.0)),
        scale=_vec3_from_call(node, "getScale", (1.0, 1.0, 1.0)),
        color_scale=_vec4_from_call(node, "getColorScale", (1.0, 1.0, 1.0, 1.0)),
    )


def _node_is_live(node: Any) -> bool:
    if node is None:
        return False
    if hasattr(node, "isEmpty"):
        try:
            return not bool(node.isEmpty())
        except TypeError:
            return True
    return True


def _vec3_from_call(node: Any, method_name: str, default: Vec3Tuple) -> Vec3Tuple:
    method = getattr(node, method_name, None)
    if method is None:
        return default
    try:
        value = method()
        return (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError, IndexError):
        return default


def _vec4_from_call(node: Any, method_name: str, default: Vec4Tuple) -> Vec4Tuple:
    method = getattr(node, method_name, None)
    if method is None:
        return default
    try:
        value = method()
        return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))
    except (TypeError, ValueError, IndexError):
        return default


def _set_pos(node: Any, value: Vec3Tuple) -> None:
    if hasattr(node, "setPos"):
        node.setPos(*value)


def _set_hpr(node: Any, value: Vec3Tuple) -> None:
    if hasattr(node, "setHpr"):
        node.setHpr(*value)
        return
    if hasattr(node, "setH"):
        node.setH(value[0])
    if hasattr(node, "setP"):
        node.setP(value[1])
    if hasattr(node, "setR"):
        node.setR(value[2])


def _set_scale(node: Any, value: Vec3Tuple) -> None:
    if hasattr(node, "setScale"):
        node.setScale(*value)


def _set_color(node: Any, value: Vec4Tuple) -> None:
    if hasattr(node, "setColorScale"):
        node.setColorScale(*value)


def _progress(track: _Track) -> float:
    if track.duration is None or track.duration <= 0:
        return 1.0
    return max(0.0, min(1.0, track.elapsed / track.duration))


def _normalize(value: Vec3Tuple) -> Vec3Tuple:
    length = math.sqrt(value[0] * value[0] + value[1] * value[1] + value[2] * value[2])
    if length <= 0.0001:
        return (0.0, -1.0, 0.0)
    return (value[0] / length, value[1] / length, value[2] / length)


def _lerp4(a: Vec4Tuple, b: Vec4Tuple, factor: float) -> Vec4Tuple:
    factor = max(0.0, min(1.0, factor))
    return tuple(a[index] + (b[index] - a[index]) * factor for index in range(4))  # type: ignore[return-value]
