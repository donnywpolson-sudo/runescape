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


def test_multiple_data_quests_track_state_independently() -> None:
    quest = QuestSystem(_multi_quest_data())

    started = quest.talk_to("trail_supplies")

    assert started.feedback == "Warden: Ready the road."
    assert quest.current_objective().text == "Trail supplies 0/2: Use the bank."

    quest.record("used_bank")

    assert quest.current_objective().text == "Trail supplies 1/2: Use the shop."

    starter = quest.talk_to_starter()

    assert starter.feedback == "Guide: Start here."
    assert quest.current_objective().text == "Starter path 0/1: Cook food."

    quest.talk_to("trail_supplies")
    quest.record("used_shop")
    completed = quest.talk_to("trail_supplies")

    assert completed.completed is True
    assert completed.feedback == "Quest complete: Trail supplies."
    assert [(reward.item_id, reward.quantity) for reward in completed.item_rewards] == [(COINS_ITEM_ID, 11)]
    assert [(reward.skill_id, reward.xp) for reward in completed.skill_rewards] == [("defence", 12)]

    quest.talk_to_starter()

    assert quest.current_objective().text == "Starter path 0/1: Cook food."


def test_quest_state_round_trip() -> None:
    quest = QuestSystem()
    quest.talk_to_starter()
    quest.record("cooked_food")
    quest.record("used_shop")

    loaded = QuestSystem()
    loaded.load_dict(quest.to_dict())

    assert loaded.state.started is True
    assert loaded.state.flags == {"cooked_food", "used_shop"}


def test_multiple_quest_state_round_trip_preserves_active_quest() -> None:
    quest = QuestSystem(_multi_quest_data())
    quest.talk_to("trail_supplies")
    quest.record("used_bank")
    saved = quest.to_dict()

    loaded = QuestSystem(_multi_quest_data())
    loaded.load_dict(saved)

    assert loaded.active_quest_id == "trail_supplies"
    assert loaded.current_objective().text == "Trail supplies 1/2: Use the shop."
    assert loaded.states["trail_supplies"].flags == {"used_bank"}


def test_legacy_single_quest_state_still_loads() -> None:
    quest = QuestSystem()

    quest.load_dict({"quest_id": "starter_path", "started": True, "flags": ["cooked_food"]})

    assert quest.active_quest_id == "starter_path"
    assert quest.state.started is True
    assert quest.state.flags == {"cooked_food"}
    assert quest.current_objective().text == "Starter path 1/8: Smelt a bar."


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


def test_app_talk_to_npc_routes_data_defined_quest_and_rewards_once() -> None:
    quest = QuestSystem(_multi_quest_data())
    feedback: list[str] = []
    updates: list[bool] = []
    app = SimpleNamespace(
        quest=quest,
        inventory=Inventory(),
        skills=Skills(
            {
                "defence": {
                    "display_name": "Defence",
                    "starting_level": 1,
                    "xp_thresholds": skill_xp_thresholds(),
                }
            }
        ),
        set_feedback=feedback.append,
        _update_hud=lambda: updates.append(True),
    )
    app._apply_quest_rewards = lambda result: GameApp._apply_quest_rewards(app, result)
    npc = SimpleNamespace(quest_id="trail_supplies", display_name="Trail Warden")

    GameApp.talk_to_npc(app, npc)
    quest.record("used_bank")
    quest.record("used_shop")
    GameApp.talk_to_npc(app, npc)
    GameApp.talk_to_npc(app, npc)

    assert feedback == [
        "Warden: Ready the road.",
        "Quest complete: Trail supplies.",
        "Warden: Road stores are ready.",
    ]
    assert app.inventory.count(COINS_ITEM_ID) == 11
    assert app.skills.xp("defence") == 12
    assert updates == [True, True, True]


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


def _multi_quest_data() -> dict[str, object]:
    return {
        "quests": [
            {
                "quest_id": "starter_path",
                "display_name": "Starter path",
                "start_text": "Guide: Start here.",
                "in_progress_text": "Guide: Missing: {missing_objectives}.",
                "completed_text": "Guide: Done.",
                "completion_text": "Quest complete: Starter path.",
                "not_started_objective": "Talk to the guide.",
                "return_objective": "Return to the guide.",
                "completed_objective": "Starter path complete.",
                "progress_format": "Starter path {completed}/{total}: {objective}.",
                "objectives": [
                    {"flag": "cooked_food", "label": "Cook food"},
                ],
                "item_rewards": [],
                "skill_rewards": [],
            },
            {
                "quest_id": "trail_supplies",
                "display_name": "Trail supplies",
                "start_text": "Warden: Ready the road.",
                "in_progress_text": "Warden: Missing: {missing_objectives}.",
                "completed_text": "Warden: Road stores are ready.",
                "completion_text": "Quest complete: Trail supplies.",
                "not_started_objective": "Talk to the Trail Warden.",
                "return_objective": "Return to the Trail Warden.",
                "completed_objective": "Trail supplies complete.",
                "progress_format": "Trail supplies {completed}/{total}: {objective}.",
                "objectives": [
                    {"flag": "used_bank", "label": "Use the bank"},
                    {"flag": "used_shop", "label": "Use the shop"},
                ],
                "item_rewards": [{"item_id": COINS_ITEM_ID, "quantity": 11}],
                "skill_rewards": [{"skill_id": "defence", "xp": 12}],
            },
        ]
    }
