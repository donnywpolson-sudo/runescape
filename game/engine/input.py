from __future__ import annotations


class InputManager:
    def __init__(self, app) -> None:
        self.app = app
        self.keys: dict[str, bool] = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "q": False,
            "e": False,
        }

    def bind(self) -> None:
        for key in self.keys:
            self.app.accept(key, self._set_key, [key, True])
            self.app.accept(f"{key}-up", self._set_key, [key, False])

        self.app.accept("wheel_up", self.app.on_mouse_wheel, [-1])
        self.app.accept("wheel_down", self.app.on_mouse_wheel, [1])
        self.app.accept("mouse1", self.app.on_left_click)
        self.app.accept("mouse3", self.app.on_right_click)
        self.app.accept("f5", self.app.save_game)
        self.app.accept("f9", self.app.load_game)
        self.app.accept("escape", self.app.userExit)

    def _set_key(self, key: str, value: bool) -> None:
        self.keys[key] = value
