from __future__ import annotations

from types import SimpleNamespace

from game.engine.app import GameApp
from game.systems.inventory import COINS_ITEM_ID
from game.systems.inventory import Inventory
from game.systems.quest import QuestState, QuestSystem, STARTER_QUEST_FLAGS
from game.systems.skills import Skills, skill_xp_thresholds


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
    assert [(reward.item_id, reward.quantity) for reward in completed.item_rewards] == [(COINS_ITEM_ID, 50)]
    assert [(reward.skill_id, reward.xp) for reward in completed.skill_rewards] == [("smithing", 40)]

    after = quest.talk_to_starter()

    assert after.completed is False
    assert "safer" in after.feedback
    assert after.item_rewards == ()
    assert after.skill_rewards == ()


def test_starter_quest_missing_objective_feedback_is_stable() -> None:
    quest = QuestSystem()
    quest.talk_to_starter()

    missing = quest.talk_to_starter()

    assert missing.completed is False
    assert "Still needed: cook food" in missing.feedback
    assert missing.item_rewards == ()
    assert missing.skill_rewards == ()


def test_starter_quest_reward_payload_grants_once_when_applied() -> None:
    quest = QuestSystem()
    quest.talk_to_starter()
    for flag in STARTER_QUEST_FLAGS:
        quest.record(flag)
    completed = quest.talk_to_starter()
    after = quest.talk_to_starter()
    app = SimpleNamespace(
        inventory=Inventory(),
        skills=Skills(
            {
                "smithing": {
                    "display_name": "Smithing",
                    "starting_level": 1,
                    "xp_thresholds": skill_xp_thresholds(),
                }
            }
        ),
    )

    GameApp._apply_quest_rewards(app, completed)
    GameApp._apply_quest_rewards(app, after)

    assert app.inventory.count(COINS_ITEM_ID) == 50
    assert app.skills.xp("smithing") == 40


def test_starter_quest_loads_text_objectives_and_rewards_from_data() -> None:
    quest = QuestSystem(_quest_data())

    started = quest.talk_to_starter()

    assert started.feedback == "Guide: Try the village work board."
    assert quest.current_objective().text == "Custom path 0/2: Gather supplies."

    quest.record("gather_supplies")

    assert quest.current_objective().text == "Custom path 1/2: Visit the shop."
    assert "gather supplies" not in quest.talk_to_starter().feedback

    quest.record("visit_shop")
    completed = quest.talk_to_starter()

    assert completed.completed is True
    assert completed.feedback == "Quest complete: Custom path."
    assert [(reward.item_id, reward.quantity) for reward in completed.item_rewards] == [(COINS_ITEM_ID, 7)]
    assert [(reward.skill_id, reward.xp) for reward in completed.skill_rewards] == [("smithing", 9)]


def test_quest_state_round_trip() -> None:
    quest = QuestSystem()
    quest.talk_to_starter()
    quest.record("cooked_food")
    quest.record("used_shop")

    loaded = QuestSystem()
    loaded.load_dict(quest.to_dict())

    assert loaded.state.started is True
    assert loaded.state.flags == {"cooked_food", "used_shop"}


def test_quest_system_accepts_existing_state_as_first_argument() -> None:
    quest = QuestSystem(QuestState(started=True, flags={"cooked_food"}))

    assert quest.state.started is True
    assert quest.state.flags == {"cooked_food"}
    assert quest.current_objective().text == "Starter path 1/8: Smelt a bar."


def test_starter_quest_objective_tracks_next_step_and_completion() -> None:
    quest = QuestSystem()

    objective = quest.current_objective()

    assert objective.text == "Talk to the Village Guide."
    assert objective.completed is False

    quest.talk_to_starter()

    assert quest.current_objective().text == "Starter path 0/8: Cook food."

    quest.record("cooked_food")

    assert quest.current_objective().text == "Starter path 1/8: Smelt a bar."

    for flag in STARTER_QUEST_FLAGS:
        quest.record(flag)

    objective = quest.current_objective()

    assert objective.text == "Return to the Village Guide."
    assert objective.completed is False

    quest.talk_to_starter()

    objective = quest.current_objective()

    assert objective.text == "Starter path complete."
    assert objective.completed is True


def _quest_data() -> dict[str, object]:
    return {
        "quests": [
            {
                "quest_id": "starter_path",
                "display_name": "Custom path",
                "start_text": "Guide: Try the village work board.",
                "in_progress_text": "Guide: Missing: {missing_objectives}.",
                "completed_text": "Guide: The work board is clear.",
                "completion_text": "Quest complete: Custom path.",
                "not_started_objective": "Talk to the work guide.",
                "return_objective": "Return to the work guide.",
                "completed_objective": "Custom path complete.",
                "progress_format": "Custom path {completed}/{total}: {objective}.",
                "objectives": [
                    {"flag": "gather_supplies", "label": "Gather supplies"},
                    {"flag": "visit_shop", "label": "Visit the shop"},
                ],
                "item_rewards": [{"item_id": COINS_ITEM_ID, "quantity": 7}],
                "skill_rewards": [{"skill_id": "smithing", "xp": 9}],
            }
        ]
    }
