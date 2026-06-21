from __future__ import annotations

from game.systems.combat_training import CombatTraining
from game.systems.skills import Skills, skill_xp_thresholds


def test_training_dummy_cooldown_blocks_spam_xp() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    training = CombatTraining(skills, cooldown_seconds=1.2, time_provider=clock)

    first = training.train()
    second = training.train()
    clock.now += 1.2
    third = training.train()

    assert first.success is True
    assert second.success is False
    assert second.feedback == "Training dummy is recovering: 1.2s"
    assert third.success is True
    assert skills.xp("attack") == 40
    assert skills.xp("strength") == 0
    assert skills.xp("defence") == 0


def test_training_style_awards_only_selected_combat_skill() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    training = CombatTraining(skills, cooldown_seconds=1.0, time_provider=clock)

    training.set_style("strength")
    result = training.train()

    assert result.feedback == "Trained Strength: +20 Strength XP"
    assert skills.xp("attack") == 0
    assert skills.xp("strength") == 20
    assert skills.xp("defence") == 0

    clock.now += 1.0
    training.set_style("defence")
    training.train()

    assert skills.xp("strength") == 20
    assert skills.xp("defence") == 20


def test_training_style_accepts_defense_alias() -> None:
    skills = Skills(_skills())
    training = CombatTraining(skills)

    training.set_style("defense")

    assert training.style == "defence"


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


def _skills() -> dict[str, dict[str, object]]:
    thresholds = skill_xp_thresholds()
    return {
        "attack": {"display_name": "Attack", "starting_level": 1, "xp_thresholds": thresholds},
        "strength": {"display_name": "Strength", "starting_level": 1, "xp_thresholds": thresholds},
        "defence": {"display_name": "Defence", "starting_level": 1, "xp_thresholds": thresholds},
    }
