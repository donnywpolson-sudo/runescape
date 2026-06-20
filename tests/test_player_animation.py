from __future__ import annotations

from game.entities.player import Player
from game.world.grid import TileGrid


def test_player_action_animation_sets_and_restores_pose() -> None:
    player = _player_with_fake_nodes()

    player.start_action_animation("woodcutting")

    assert player.action_animation == "woodcutting"
    assert player.parts["right_arm"].hpr != (0.0, 0.0, 0.0)
    assert player.parts["tool"].hpr != (-16.0, 0.0, -10.0)

    assert player.stop_action_animation()
    assert player.action_animation is None
    assert player.parts["right_arm"].hpr == (0.0, 0.0, 0.0)
    assert player.parts["tool"].hpr == (-16.0, 0.0, -10.0)


def test_player_movement_stops_action_animation() -> None:
    player = _player_with_fake_nodes()

    player.start_action_animation("fishing")
    player.set_path([(1, 1), (1, 2)])

    assert player.action_animation is None
    assert player.path == [(1, 2)]


def _player_with_fake_nodes() -> Player:
    player = Player(TileGrid(4, 4), (1, 1))
    player.node = _FakeNode()
    player.parts = {
        key: _FakeNode()
        for key in ("left_leg", "right_leg", "left_arm", "right_arm", "body", "head", "tool")
    }
    return player


class _FakeNode:
    def __init__(self) -> None:
        self.hpr = (0.0, 0.0, 0.0)
        self.pos = (0.0, 0.0, 0.0)
        self.heading = 0.0

    def setHpr(self, h: float, p: float, r: float) -> None:
        self.hpr = (round(h, 3), round(p, 3), round(r, 3))

    def setP(self, p: float) -> None:
        self.hpr = (self.hpr[0], round(p, 3), self.hpr[2])

    def setPos(self, *args: object) -> None:
        if len(args) == 1:
            value = args[0]
            self.pos = (round(float(value[0]), 3), round(float(value[1]), 3), round(float(value[2]), 3))  # type: ignore[index]
        elif len(args) == 3:
            self.pos = (round(float(args[0]), 3), round(float(args[1]), 3), round(float(args[2]), 3))

    def setH(self, h: float) -> None:
        self.heading = round(h, 3)
