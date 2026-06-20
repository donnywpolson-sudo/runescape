from __future__ import annotations

from game.systems.quest import QuestSystem, STARTER_QUEST_FLAGS


def test_starter_quest_starts_tracks_flags_and_completes_once() -> None:
    quest = QuestSystem()

    started = quest.talk_to_starter()

    assert "Cook food" in started.feedback
    assert quest.state.started is True

    for flag in STARTER_QUEST_FLAGS:
        quest.record(flag)

    completed = quest.talk_to_starter()

    assert completed.completed is True
    assert "Quest complete" in completed.feedback

    after = quest.talk_to_starter()

    assert after.completed is False
    assert "safer" in after.feedback


def test_quest_state_round_trip() -> None:
    quest = QuestSystem()
    quest.talk_to_starter()
    quest.record("cooked_food")
    quest.record("used_shop")

    loaded = QuestSystem()
    loaded.load_dict(quest.to_dict())

    assert loaded.state.started is True
    assert loaded.state.flags == {"cooked_food", "used_shop"}
