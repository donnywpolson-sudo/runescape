from __future__ import annotations

from game.systems.combat import CombatSystem, DropStack, MobDefinition
from game.systems.skills import Skills, skill_xp_thresholds
from game.world.grid import TileGrid


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_combat_auto_attacks_until_mob_dies_and_respawns() -> None:
    clock = FakeClock()
    system = CombatSystem([_mob()], time_provider=clock)
    grid = TileGrid(5, 5)

    started = system.start_attack("mob_01", (1, 2), grid, set())

    assert started.success is True
    assert started.pending is True
    assert started.feedback == "Attacking Worn dummy: 2/2 HP; you: 10/10 HP; 1.0s"

    clock.now += 1.0
    first_hit = system.update()

    assert first_hit is not None
    assert first_hit.pending is True
    assert first_hit.killed is False
    assert system.states["mob_01"].hitpoints == 1

    clock.now += 1.0
    killed = system.update()

    assert killed is not None
    assert killed.killed is True
    assert killed.drops == (DropStack("coins", 3), DropStack("wooden_splinters", 1))
    assert system.is_dead("mob_01") is True

    clock.now += 5.0
    system.refresh_all()

    assert system.is_dead("mob_01") is False
    assert system.to_dict() == {}


def test_combat_state_round_trip_preserves_dead_mob() -> None:
    clock = FakeClock()
    system = CombatSystem([_mob()], time_provider=clock)
    grid = TileGrid(5, 5)
    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 2.0
    assert system.update() is not None
    clock.now += 2.0
    assert system.update() is not None

    loaded = CombatSystem([_mob()], time_provider=clock)
    loaded.load_dict(system.to_dict())

    assert loaded.is_dead("mob_01") is True


def test_combat_damages_player_grants_xp_and_can_heal() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    system = CombatSystem([_mob(hitpoints=3, level=3)], skills=skills, time_provider=clock)
    grid = TileGrid(5, 5)

    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = system.update()

    assert result is not None
    assert result.enemy_damage == 1
    assert result.feedback == "Hit Worn dummy: 2/3 HP left; Worn dummy hit you for 1; you: 9/10 HP"
    assert system.current_hitpoints == 9
    assert skills.xp("attack") == 4
    assert skills.xp("strength") == 0
    assert skills.xp("defence") == 0
    assert skills.xp("hitpoints") == 1

    assert system.heal(3) == 1
    assert system.current_hitpoints == 10


def test_combat_training_style_controls_combat_xp() -> None:
    clock = FakeClock()
    skills = Skills(_skills())
    system = CombatSystem([_mob(hitpoints=3, level=1)], skills=skills, time_provider=clock)
    system.set_training_style("strength")
    grid = TileGrid(5, 5)

    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = system.update()

    assert result is not None
    assert skills.xp("attack") == 0
    assert skills.xp("strength") == 4
    assert skills.xp("defence") == 0
    assert skills.xp("hitpoints") == 1


def test_combat_reports_player_death() -> None:
    clock = FakeClock()
    system = CombatSystem([_mob(hitpoints=4, level=9)], current_hitpoints=2, time_provider=clock)
    grid = TileGrid(5, 5)

    system.start_attack("mob_01", (1, 2), grid, set())
    clock.now += 1.0
    result = system.update()

    assert result is not None
    assert result.player_dead is True
    assert result.feedback == "You were defeated by Worn dummy; Worn dummy: 3/4 HP; you: 0/10 HP"
    assert system.current_hitpoints == 0


def _mob(hitpoints: int = 2, level: int = 1) -> MobDefinition:
    return MobDefinition(
        mob_id="mob_01",
        display_name="Worn dummy",
        level=level,
        hitpoints=hitpoints,
        attack_seconds=1.0,
        respawn_seconds=5.0,
        position=(2, 2),
        drops=(DropStack("coins", 3), DropStack("wooden_splinters", 1)),
    )


def _skills() -> dict[str, dict[str, object]]:
    thresholds = skill_xp_thresholds()
    return {
        "attack": {"display_name": "Attack", "starting_level": 1, "xp_thresholds": thresholds},
        "strength": {"display_name": "Strength", "starting_level": 1, "xp_thresholds": thresholds},
        "defence": {"display_name": "Defence", "starting_level": 1, "xp_thresholds": thresholds},
        "hitpoints": {"display_name": "Hitpoints", "starting_level": 10, "xp_thresholds": thresholds},
    }
