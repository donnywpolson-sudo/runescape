from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode


class Hud:
    def __init__(self) -> None:
        self.stats = OnscreenText(
            text="",
            pos=(-1.32, 0.92),
            scale=0.045,
            align=TextNode.ALeft,
            fg=(1, 1, 1, 1),
            mayChange=True,
        )
        self.help = OnscreenText(
            text=(
                "WASD camera | Q/E rotate | Wheel zoom | Left click move | "
                "Right click interact | F5 save | F9 load | Esc quit"
            ),
            pos=(-1.32, -0.94),
            scale=0.038,
            align=TextNode.ALeft,
            fg=(0.92, 0.92, 0.86, 1),
            mayChange=False,
        )
        self.feedback = OnscreenText(
            text="",
            pos=(-1.32, 0.68),
            scale=0.045,
            align=TextNode.ALeft,
            fg=(1.0, 0.86, 0.35, 1),
            mayChange=True,
        )

    def update(self, lines: list[str]) -> None:
        self.stats.setText("\n".join(lines))

    def set_feedback(self, message: str) -> None:
        self.feedback.setText(message)
