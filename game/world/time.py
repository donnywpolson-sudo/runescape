from __future__ import annotations

from dataclasses import dataclass

from game import settings

MINUTES_PER_DAY = 24 * 60


@dataclass
class GameTime:
    day: int = settings.START_DAY
    minute: float = float(settings.START_MINUTE)

    def update(self, dt: float) -> None:
        self.minute += dt * settings.GAME_MINUTES_PER_REAL_SECOND
        while self.minute >= MINUTES_PER_DAY:
            self.minute -= MINUTES_PER_DAY
            self.day += 1

    def display(self) -> str:
        total = int(self.minute) % MINUTES_PER_DAY
        hour = total // 60
        minute = total % 60
        return f"Day {self.day} {hour:02d}:{minute:02d}"

    def to_dict(self) -> dict[str, int | float]:
        return {"day": self.day, "minute": self.minute}

    def load_dict(self, data: dict[str, int | float]) -> None:
        self.day = int(data.get("day", self.day))
        self.minute = float(data.get("minute", self.minute))
