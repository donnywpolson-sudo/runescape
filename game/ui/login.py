from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from direct.gui.DirectGui import DirectButton, DirectEntry, DirectFrame, DirectLabel

from game import settings
from game.engine import auth, save


LOGGER = logging.getLogger(__name__)

PANEL = (0.22, 0.15, 0.08, 0.94)
PANEL_DARK = (0.10, 0.07, 0.04, 1.0)
BUTTON = (0.48, 0.34, 0.16, 1.0)
BUTTON_HOVER = (0.60, 0.43, 0.21, 1.0)
TEXT = (0.96, 0.88, 0.68, 1.0)
GOLD = (1.0, 0.78, 0.28, 1.0)


class LoginScreen:
    def __init__(
        self,
        app: Any,
        on_success: Callable[[str, dict[str, Any], str], None],
    ) -> None:
        self.app = app
        self.on_success = on_success
        self.widgets: list[Any] = []
        self._build()

    def set_status(self, message: str) -> None:
        self.status["text"] = message

    def destroy(self) -> None:
        for widget in self.widgets:
            widget.destroy()
        self.widgets.clear()

    def _build(self) -> None:
        frame = DirectFrame(
            frameColor=PANEL,
            frameSize=(-0.62, 0.62, -0.38, 0.38),
            pos=(0, 0, 0),
        )
        title = DirectLabel(
            parent=frame,
            text="RuneScape Valley",
            scale=0.075,
            pos=(0, 0, 0.27),
            frameColor=(0, 0, 0, 0),
            text_fg=GOLD,
        )
        username_label = DirectLabel(
            parent=frame,
            text="Username",
            scale=0.038,
            pos=(-0.34, 0, 0.19),
            frameColor=(0, 0, 0, 0),
            text_fg=TEXT,
        )
        self.username = DirectEntry(
            parent=frame,
            initialText="",
            width=18,
            scale=0.052,
            pos=(-0.46, 0, 0.12),
            frameColor=PANEL_DARK,
            text_fg=TEXT,
            focus=1,
            command=self._login,
        )
        password_label = DirectLabel(
            parent=frame,
            text="Password",
            scale=0.038,
            pos=(-0.34, 0, 0.05),
            frameColor=(0, 0, 0, 0),
            text_fg=TEXT,
        )
        self.password = DirectEntry(
            parent=frame,
            initialText="",
            width=18,
            scale=0.052,
            pos=(-0.46, 0, -0.02),
            frameColor=PANEL_DARK,
            text_fg=TEXT,
            obscured=1,
            command=self._login,
        )
        login_button = DirectButton(
            parent=frame,
            text="Login",
            scale=0.052,
            pos=(-0.18, 0, -0.17),
            frameColor=(BUTTON, BUTTON_HOVER, BUTTON_HOVER, BUTTON),
            text_fg=TEXT,
            command=self._login,
        )
        register_button = DirectButton(
            parent=frame,
            text="Register",
            scale=0.052,
            pos=(0.20, 0, -0.17),
            frameColor=(BUTTON, BUTTON_HOVER, BUTTON_HOVER, BUTTON),
            text_fg=TEXT,
            command=self._register,
        )
        quit_button = DirectButton(
            parent=frame,
            text="Quit",
            scale=0.046,
            pos=(0, 0, -0.27),
            frameColor=(BUTTON, BUTTON_HOVER, BUTTON_HOVER, BUTTON),
            text_fg=TEXT,
            command=self.app.userExit,
        )
        self.status = DirectLabel(
            parent=frame,
            text="Local account only",
            scale=0.042,
            pos=(0, 0, -0.34),
            frameColor=(0, 0, 0, 0),
            text_fg=GOLD,
        )
        self.widgets.extend([
            frame,
            title,
            username_label,
            self.username,
            password_label,
            self.password,
            login_button,
            register_button,
            quit_button,
            self.status,
        ])

    def _credentials(self) -> tuple[str, str] | None:
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            self.set_status("Enter a username and password")
            return None
        return username, password

    def _login(self, *_args: object) -> None:
        credentials = self._credentials()
        if credentials is None:
            return
        username, password = credentials
        try:
            account = auth.login_user(username, password, settings.USERS_DB_PATH)
        except ValueError as exc:
            self.set_status(str(exc))
            return
        except OSError:
            LOGGER.exception("Login failed")
            self.set_status("Login failed")
            return

        if account is None:
            self.set_status("Invalid username or password")
            return
        self._enter(account.username, "Logged in")

    def _register(self) -> None:
        credentials = self._credentials()
        if credentials is None:
            return
        username, password = credentials
        try:
            account = auth.register_user(username, password, settings.USERS_DB_PATH)
        except auth.UsernameAlreadyExists:
            self.set_status("Username already exists")
            return
        except ValueError as exc:
            self.set_status(str(exc))
            return
        except OSError:
            LOGGER.exception("Registration failed")
            self.set_status("Registration failed")
            return
        self._enter(account.username, "Registered new account")

    def _enter(self, username: str, message: str) -> None:
        try:
            state, created = save.load_or_create_save(username, settings.SAVES_DIR)
        except OSError:
            LOGGER.exception("Save load failed for %s", username)
            self.set_status("Could not load save")
            return

        self.destroy()
        detail = "New character created" if created else message
        self.on_success(username, state, detail)
