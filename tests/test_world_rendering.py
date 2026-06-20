from __future__ import annotations

import math

from panda3d.core import NodePath

from game.systems.combat import MobState
from game.systems.gathering import ResourceNodeState
from game.world import visuals
from game.world.map import TERRAIN_CHUNK_SIZE, WorldMap


def test_large_world_render_chunks_terrain_and_keeps_interactives_live() -> None:
    world = WorldMap(
        {
            "width": 100,
            "height": 100,
            "blocked_tiles": [[4, 4]],
            "resource_nodes": [],
            "decorations": [
                {"id": "sign_01", "kind": "signpost", "position": [5, 5]},
            ],
            "shop": {"id": "shop_01", "name": "General Buyer", "tile": [23, 15]},
        }
    )
    parent = NodePath("test_render")

    world.render(parent)

    expected_chunks = math.ceil(100 / TERRAIN_CHUNK_SIZE) ** 2
    assert len(world.terrain_chunks) == expected_chunks
    assert all(chunk.getName().startswith("terrain_chunk_") for chunk in world.terrain_chunks)

    shop = world.get_object("shop_01")
    assert shop is not None
    assert shop.node is not None
    assert shop.node.getParent().getName() == "world"
    assert world.object_at((23, 15)) is shop
    assert world.target_at((23, 15)) is shop

    sign = world.target_at((5, 5))
    assert sign is not None
    assert sign.object_id == "sign_01"
    assert sign.node is not None

    rocks = world.target_at((4, 4))
    assert rocks is not None
    assert rocks.object_id == "blocked_4_4"
    assert rocks.node is not None


def test_asset_renderer_hook_can_override_world_object_rendering() -> None:
    calls: list[tuple[str, str, int]] = []

    def render_shop_asset(holder, obj, _resource_node, _resource_state, tier) -> None:
        calls.append((holder.getName(), obj.object_id, tier))
        holder.attachNewNode("asset_marker")

    visuals.register_asset_renderer("shop", render_shop_asset)
    try:
        world = WorldMap(
            {
                "width": 4,
                "height": 4,
                "blocked_tiles": [],
                "resource_nodes": [],
                "shop": {"id": "shop_01", "name": "General Buyer", "tile": [1, 1]},
            }
        )
        parent = NodePath("test_render")

        world.render(parent)

        shop = world.get_object("shop_01")
        assert shop is not None
        assert calls == [("shop_01", "shop_01", 1)]
        assert shop.node.find("**/asset_marker").isEmpty() is False
    finally:
        visuals.register_asset_renderer("shop", None)


def test_grass_tiles_avoid_high_contrast_repeating_slabs() -> None:
    parent = NodePath("test_render")

    visuals.render_terrain_tile(parent, (2, 3), "grass", set())

    tile = parent.find("**/tile_2_3")
    assert tile.isEmpty() is False
    assert tile.find("**/grass_base").isEmpty() is False
    assert tile.find("**/grass_cross_tile_patch").isEmpty() is True
    assert tile.find("**/grass_dirt_blend").isEmpty() is True
    assert tile.find("**/grass_edge_blade_0").isEmpty() is True


def test_ore_node_exposes_material_color_and_depleted_state() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [
                {
                    "node_id": "copper_rock_01",
                    "node_type": "copper_rock",
                    "display_name": "Copper rock",
                    "skill_id": "mining",
                    "required_level": 1,
                    "xp_reward": 20,
                    "item_reward": "copper_ore",
                    "quantity_reward": 1,
                    "position": [1, 1],
                    "blocks_movement": True,
                    "depleted_state": "depleted_rock",
                    "respawn_seconds": 30,
                    "base_gather_seconds": 2.2,
                }
            ],
        }
    )
    parent = NodePath("test_render")

    world.render(parent)

    rock = world.get_object("copper_rock_01")
    assert rock is not None and rock.node is not None
    vein = rock.node.find("**/copper_rock_01_ore_vein_primary")
    assert vein.isEmpty() is False
    assert vein.getTag("resource_color") == "0.76,0.35,0.15,1.00"

    world.apply_resource_states({"copper_rock_01": ResourceNodeState(depleted=True, respawn_at=200.0)})

    rock = world.get_object("copper_rock_01")
    assert rock is not None and rock.node is not None
    assert rock.node.find("**/copper_rock_01_ore_vein_primary").isEmpty() is True
    assert rock.node.find("**/copper_rock_01_depleted_collapsed_core").isEmpty() is False


def test_mob_hp_bar_uses_current_to_max_hitpoint_ratio() -> None:
    world = WorldMap(
        {
            "width": 4,
            "height": 4,
            "blocked_tiles": [],
            "water_tiles": [],
            "resource_nodes": [],
            "mobs": [
                {
                    "mob_id": "mob_01",
                    "display_name": "Worn dummy",
                    "level": 1,
                    "hitpoints": 4,
                    "attack_seconds": 1.0,
                    "respawn_seconds": 5.0,
                    "position": [1, 1],
                    "drops": [],
                }
            ],
        }
    )
    world.apply_mob_states({"mob_01": MobState(hitpoints=2)})
    parent = NodePath("test_render")

    world.render(parent)

    mob = world.get_object("mob_01")
    assert mob is not None and mob.node is not None
    fill = mob.node.find("**/mob_01_hp_bar_fill")
    assert fill.isEmpty() is False
    assert round(fill.getSx(), 2) == 0.50
    assert mob.node.find("**/mob_01_hp_pip_0").isEmpty() is True
