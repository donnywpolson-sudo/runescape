from __future__ import annotations

import math
from typing import TypeVar

from panda3d.core import LineSegs, NodePath

from game import settings
from game.style import Color, WorldPalette as C
from game.systems.gathering import ResourceNode, ResourceNodeState
from game.world.grid import Tile
from game.world.objects import WorldObject, make_box, make_cone, make_cylinder, make_quad

T = TypeVar("T")


CARDINAL_DIRECTIONS: dict[str, tuple[int, int]] = {
    "west": (-1, 0),
    "east": (1, 0),
    "south": (0, -1),
    "north": (0, 1),
}


def render_terrain_tile(parent: NodePath, tile: Tile, terrain: str, edge_dirs: set[str]) -> None:
    x, y = tile
    holder = parent.attachNewNode(f"tile_{x}_{y}")
    holder.setPos(x * settings.TILE_SIZE, y * settings.TILE_SIZE, -0.035 if terrain == "water" else 0.0)

    if terrain == "water":
        _render_water_tile(holder, tile, edge_dirs)
    elif terrain == "dirt":
        _render_dirt_tile(holder, tile, edge_dirs)
    else:
        _render_grass_tile(holder, tile)


def render_static_obstacle(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.52, 0.36)

    base = make_box(f"{name}_base", (0.72, 0.66, 0.26), C.STONE_DARK)
    base.reparentTo(holder)
    base.setH(18)

    crest = make_cone(f"{name}_crest", 0.43, 0.42, 5, C.STONE)
    crest.reparentTo(holder)
    crest.setZ(0.22)
    crest.setH(-12)

    chip = make_box(f"{name}_chip", (0.22, 0.18, 0.10), C.STONE_LIGHT)
    chip.reparentTo(holder)
    chip.setPos(0.25, -0.18, 0.05)
    chip.setH(28)


def render_world_object(
    holder: NodePath,
    obj: WorldObject,
    resource_node: ResourceNode | None,
    resource_state: ResourceNodeState,
) -> None:
    render_kind = obj.kind
    tier = 1
    if resource_node is not None:
        tier = resource_node.required_level
        if resource_state.depleted:
            render_kind = resource_node.depleted_state
        elif resource_node.skill_id == "woodcutting":
            render_kind = "tree"
        elif resource_node.skill_id == "mining":
            render_kind = "ore_rock"
        elif resource_node.skill_id == "fishing":
            render_kind = "fishing_spot"

    if resource_node is not None and not resource_state.depleted:
        ring = make_ground_ring(f"{obj.object_id}_ready_ring", 0.43, C.RESOURCE_RING, thickness=1.4)
        ring.reparentTo(holder)
        ring.setZ(0.035)

    if render_kind == "tree":
        _render_tree(holder, obj.object_id, tier)
    elif render_kind == "stump":
        _render_stump(holder, obj.object_id, resource_state)
    elif render_kind == "ore_rock":
        _render_ore_rock(holder, obj.object_id, tier)
    elif render_kind == "depleted_rock":
        _render_depleted_rock(holder, obj.object_id, resource_state)
    elif render_kind == "fishing_spot":
        _render_fishing_spot(holder, obj.object_id, tier)
    elif render_kind == "quiet_water":
        _render_quiet_water(holder, obj.object_id, resource_state)
    elif render_kind == "shop":
        _render_shop(holder, obj.object_id)
    elif render_kind == "bank":
        _render_bank(holder, obj.object_id)
    elif render_kind == "cooking_range":
        _render_cooking_range(holder, obj.object_id)
    elif render_kind == "combat_dummy":
        _render_combat_dummy(holder, obj.object_id)
    elif render_kind == "furnace":
        _render_furnace(holder, obj.object_id)
    elif render_kind == "anvil":
        _render_anvil(holder, obj.object_id)
    elif render_kind == "npc":
        _render_quest_npc(holder, obj.object_id)
    elif render_kind == "mob":
        _render_mob(holder, obj)
    elif render_kind == "ground_item":
        _render_ground_item(holder, obj)


def render_decoration(holder: NodePath, decoration_id: str, kind: str) -> None:
    if kind == "fence":
        _render_fence(holder, decoration_id)
    elif kind == "signpost":
        _render_signpost(holder, decoration_id)
    elif kind == "crate":
        _render_crate(holder, decoration_id)
    elif kind == "barrel":
        _render_barrel(holder, decoration_id)
    elif kind == "mushroom":
        _render_mushroom(holder, decoration_id)
    elif kind == "bush":
        _render_bush(holder, decoration_id)
    elif kind == "ruins":
        _render_ruins(holder, decoration_id)
    elif kind == "lamp":
        _render_lamp(holder, decoration_id)
    elif kind == "dock":
        _render_dock(holder, decoration_id)
    else:
        _render_bush(holder, decoration_id)


def render_player_model(parent: NodePath) -> dict[str, NodePath]:
    parts: dict[str, NodePath] = {}
    _shadow(parent, "player_shadow", 0.32, 0.20)

    left_boot = make_box("player_left_boot", (0.14, 0.18, 0.10), C.PLAYER_BOOT)
    left_boot.reparentTo(parent)
    left_boot.setPos(-0.09, -0.02, 0.02)
    parts["left_boot"] = left_boot

    right_boot = make_box("player_right_boot", (0.14, 0.18, 0.10), C.PLAYER_BOOT)
    right_boot.reparentTo(parent)
    right_boot.setPos(0.09, -0.02, 0.02)
    parts["right_boot"] = right_boot

    left_leg = make_box("player_left_leg", (0.11, 0.12, 0.34), C.PLAYER_TROUSERS)
    left_leg.reparentTo(parent)
    left_leg.setPos(-0.08, 0.0, 0.11)
    parts["left_leg"] = left_leg

    right_leg = make_box("player_right_leg", (0.11, 0.12, 0.34), C.PLAYER_TROUSERS)
    right_leg.reparentTo(parent)
    right_leg.setPos(0.08, 0.0, 0.11)
    parts["right_leg"] = right_leg

    body = make_box("player_body", (0.36, 0.25, 0.44), C.PLAYER_TUNIC)
    body.reparentTo(parent)
    body.setZ(0.44)
    parts["body"] = body

    belt = make_box("player_belt", (0.40, 0.27, 0.055), C.WOOD_DARK)
    belt.reparentTo(parent)
    belt.setZ(0.42)

    left_arm = make_box("player_left_arm", (0.09, 0.10, 0.36), C.PLAYER_SLEEVE)
    left_arm.reparentTo(parent)
    left_arm.setPos(-0.26, 0.0, 0.47)
    parts["left_arm"] = left_arm

    right_arm = make_box("player_right_arm", (0.09, 0.10, 0.36), C.PLAYER_SLEEVE)
    right_arm.reparentTo(parent)
    right_arm.setPos(0.26, 0.0, 0.47)
    parts["right_arm"] = right_arm

    tool = parent.attachNewNode("player_tool")
    tool.setPos(0.31, -0.05, 0.26)
    tool.setHpr(-16, 0, -10)
    handle = make_box("player_tool_handle", (0.045, 0.055, 0.42), C.WOOD_LIGHT)
    handle.reparentTo(tool)
    head = make_box("player_tool_head", (0.16, 0.060, 0.08), C.STONE_LIGHT)
    head.reparentTo(tool)
    head.setPos(-0.04, -0.005, 0.36)
    parts["tool"] = tool

    head = make_cylinder("player_head", 0.16, 0.21, 8, C.SKIN)
    head.reparentTo(parent)
    head.setZ(0.80)

    hair = make_cone("player_hair", 0.18, 0.12, 8, C.HAIR)
    hair.reparentTo(parent)
    hair.setZ(1.00)

    nose = make_box("player_nose", (0.05, 0.08, 0.04), C.SKIN)
    nose.reparentTo(parent)
    nose.setPos(0.0, -0.15, 0.89)
    parts["head"] = head
    return parts


def make_ground_ring(name: str, radius: float, color: Color, *, thickness: float = 2.0) -> NodePath:
    lines = LineSegs(name)
    lines.setColor(*color)
    lines.setThickness(thickness)
    segments = 32
    for index in range(segments + 1):
        angle = math.tau * index / segments
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        if index == 0:
            lines.moveTo(x, y, 0.0)
        else:
            lines.drawTo(x, y, 0.0)
    return NodePath(lines.create())


def make_tile_marker(name: str, color: Color, *, radius: float = 0.46) -> NodePath:
    marker = make_ground_ring(name, radius, color, thickness=3.0)
    marker.hide()
    return marker


def world_tint(minute: float) -> tuple[Color, Color]:
    hour = (minute / 60.0) % 24.0
    if 5.0 <= hour < 7.0:
        factor = (hour - 5.0) / 2.0
        tint = _lerp_color((0.70, 0.58, 0.48, 1.0), (1.0, 0.98, 0.90, 1.0), factor)
        sky = _lerp_color((0.30, 0.35, 0.48, 1.0), (0.56, 0.70, 0.84, 1.0), factor)
    elif 7.0 <= hour < 18.0:
        tint = (1.0, 0.98, 0.90, 1.0)
        sky = (0.56, 0.70, 0.84, 1.0)
    elif 18.0 <= hour < 20.0:
        factor = (hour - 18.0) / 2.0
        tint = _lerp_color((1.0, 0.98, 0.90, 1.0), (0.64, 0.52, 0.48, 1.0), factor)
        sky = _lerp_color((0.56, 0.70, 0.84, 1.0), (0.24, 0.24, 0.36, 1.0), factor)
    else:
        tint = (0.54, 0.56, 0.68, 1.0)
        sky = (0.12, 0.15, 0.24, 1.0)
    return tint, sky


def _render_grass_tile(holder: NodePath, tile: Tile) -> None:
    base = make_quad("grass_base", settings.TILE_SIZE, _palette_color(tile, C.GRASS))
    base.reparentTo(holder)

    if _hash(tile, 3) == 0:
        tuft = make_box("grass_tuft", (0.16, 0.04, 0.06), C.GRASS_LIGHT)
        tuft.reparentTo(holder)
        tuft.setPos(0.27, 0.34, 0.015)
        tuft.setH(28)
    if _hash(tile, 5) == 0:
        patch = make_box("grass_dark_patch", (0.30, 0.09, 0.012), C.GRASS_DARK)
        patch.reparentTo(holder)
        patch.setPos(0.34, 0.72, 0.008)
        patch.setH(-23)
    if _hash(tile, 7) == 0:
        stone = make_box("grass_pebble", (0.11, 0.08, 0.025), C.STONE_DARK)
        stone.reparentTo(holder)
        stone.setPos(0.70, 0.62, 0.01)
        stone.setH(-18)
    if _hash(tile, 11) == 0:
        flower = make_box("grass_flower", (0.05, 0.05, 0.045), C.FLOWER_YELLOW)
        flower.reparentTo(holder)
        flower.setPos(0.60, 0.30, 0.015)
    if _hash(tile, 17) == 0:
        blade = make_box("grass_blade", (0.05, 0.20, 0.055), C.GRASS_LIGHT)
        blade.reparentTo(holder)
        blade.setPos(0.76, 0.24, 0.012)
        blade.setH(42)


def _render_dirt_tile(holder: NodePath, tile: Tile, edge_dirs: set[str]) -> None:
    base = make_quad("dirt_base", settings.TILE_SIZE, C.SHORE)
    base.reparentTo(holder)

    path = make_box("dirt_path", (0.92, 0.92, 0.018), _palette_color(tile, C.DIRT))
    path.reparentTo(holder)
    path.setPos(0.50, 0.50, 0.0)

    if _hash(tile, 6) == 0:
        worn = make_box("dirt_worn_strip", (0.58, 0.055, 0.022), C.DIRT_LIGHT)
        worn.reparentTo(holder)
        worn.setPos(0.48, 0.48, 0.009)
        worn.setH(34)

    for edge in edge_dirs:
        if edge in {"west", "east"}:
            strip = make_box(f"dirt_edge_{edge}", (0.08, 1.0, 0.024), C.DIRT_EDGE)
            strip.setPos(0.04 if edge == "west" else 0.96, 0.50, 0.006)
        else:
            strip = make_box(f"dirt_edge_{edge}", (1.0, 0.08, 0.024), C.DIRT_EDGE)
            strip.setPos(0.50, 0.04 if edge == "south" else 0.96, 0.006)
        strip.reparentTo(holder)

    if _hash(tile, 4) == 0:
        pebble = make_box("dirt_pebble", (0.10, 0.07, 0.025), C.DIRT_LIGHT)
        pebble.reparentTo(holder)
        pebble.setPos(0.34, 0.68, 0.012)
        pebble.setH(17)


def _render_water_tile(holder: NodePath, tile: Tile, edge_dirs: set[str]) -> None:
    base = make_quad("water_base", settings.TILE_SIZE, _palette_color(tile, C.WATER))
    base.reparentTo(holder)

    if _hash(tile, 2) == 0:
        ripple = make_box("water_ripple", (0.42, 0.035, 0.010), C.WATER_RIPPLE)
        ripple.reparentTo(holder)
        ripple.setPos(0.50, 0.50, 0.012)
        ripple.setH(12)
    if _hash(tile, 5) == 0:
        shimmer = make_box("water_shimmer", (0.30, 0.018, 0.009), C.WATER_SHIMMER)
        shimmer.reparentTo(holder)
        shimmer.setPos(0.58, 0.32, 0.014)
        shimmer.setH(-18)

    for edge in edge_dirs:
        if edge in {"west", "east"}:
            strip = make_box(f"shore_{edge}", (0.05, 1.0, 0.012), C.SHORE)
            strip.setPos(0.025 if edge == "west" else 0.975, 0.50, 0.018)
        else:
            strip = make_box(f"shore_{edge}", (1.0, 0.05, 0.012), C.SHORE)
            strip.setPos(0.50, 0.025 if edge == "south" else 0.975, 0.018)
        strip.reparentTo(holder)


def _render_tree(holder: NodePath, name: str, tier: int) -> None:
    leaf_dark, leaf, leaf_light = _tree_colors(tier)
    _shadow(holder, f"{name}_shadow", 0.56, 0.34)

    trunk = make_cylinder(f"{name}_trunk", 0.13, 0.90, 7, C.TRUNK)
    trunk.reparentTo(holder)
    trunk.setPos(0.0, 0.0, 0.02)

    trunk_side = make_cylinder(f"{name}_trunk_shadow", 0.08, 0.92, 7, C.TRUNK_DARK)
    trunk_side.reparentTo(holder)
    trunk_side.setPos(-0.05, -0.04, 0.02)

    branch = make_box(f"{name}_branch", (0.10, 0.36, 0.08), C.TRUNK_DARK)
    branch.reparentTo(holder)
    branch.setPos(0.06, -0.04, 0.68)
    branch.setH(-34)

    lower = make_cone(f"{name}_leaves_lower", 0.66, 0.62, 7, leaf_dark)
    lower.reparentTo(holder)
    lower.setZ(0.58)
    lower.setH(18)

    side = make_cone(f"{name}_leaves_side", 0.38, 0.42, 6, leaf)
    side.reparentTo(holder)
    side.setPos(-0.28, 0.12, 0.78)
    side.setH(-28)

    middle = make_cone(f"{name}_leaves_middle", 0.52, 0.62, 7, leaf)
    middle.reparentTo(holder)
    middle.setZ(0.94)
    middle.setH(-10)

    top = make_cone(f"{name}_leaves_top", 0.34, 0.46, 7, leaf_light)
    top.reparentTo(holder)
    top.setZ(1.30)
    top.setH(8)


def _render_stump(holder: NodePath, name: str, state: ResourceNodeState) -> None:
    _shadow(holder, f"{name}_shadow", 0.30, 0.18)
    stump = make_cylinder(f"{name}_stump", 0.20, 0.24, 8, C.STUMP)
    stump.reparentTo(holder)
    cut = make_cylinder(f"{name}_cut", 0.17, 0.03, 8, C.STUMP_TOP)
    cut.reparentTo(holder)
    cut.setZ(0.24)
    notch = make_box(f"{name}_notch", (0.18, 0.05, 0.05), C.TRUNK_DARK)
    notch.reparentTo(holder)
    notch.setPos(0.04, -0.16, 0.23)
    notch.setH(18)
    _respawn_glow(holder, name, state, 0.31)


def _render_ore_rock(holder: NodePath, name: str, tier: int) -> None:
    rock_dark, rock_light, vein_color = _rock_colors(tier)
    _shadow(holder, f"{name}_shadow", 0.48, 0.30)

    base = make_box(f"{name}_rock_base", (0.72, 0.64, 0.34), rock_dark)
    base.reparentTo(holder)
    base.setH(15)

    cap = make_cone(f"{name}_cap", 0.48, 0.40, 5, rock_light)
    cap.reparentTo(holder)
    cap.setZ(0.30)
    cap.setH(-8)

    vein = make_box(f"{name}_ore_vein", (0.17, 0.23, 0.09), vein_color)
    vein.reparentTo(holder)
    vein.setPos(0.15, -0.18, 0.31)
    vein.setH(30)

    shard = make_box(f"{name}_ore_shard", (0.12, 0.10, 0.08), vein_color)
    shard.reparentTo(holder)
    shard.setPos(-0.20, 0.12, 0.25)
    shard.setH(-20)

    rear = make_box(f"{name}_rear_facet", (0.28, 0.22, 0.18), rock_light)
    rear.reparentTo(holder)
    rear.setPos(-0.21, 0.20, 0.16)
    rear.setH(42)

    chip = make_box(f"{name}_bright_chip", (0.08, 0.07, 0.06), vein_color)
    chip.reparentTo(holder)
    chip.setPos(0.30, 0.05, 0.20)
    chip.setH(14)


def _render_depleted_rock(holder: NodePath, name: str, state: ResourceNodeState) -> None:
    _shadow(holder, f"{name}_shadow", 0.42, 0.25)
    rock = make_box(f"{name}_depleted_rock", (0.64, 0.54, 0.22), C.STONE_DARK)
    rock.reparentTo(holder)
    rock.setH(-18)
    chip = make_box(f"{name}_depleted_chip", (0.24, 0.14, 0.08), C.STONE)
    chip.reparentTo(holder)
    chip.setPos(0.16, -0.12, 0.20)
    chip.setH(24)
    dust = make_box(f"{name}_depleted_dust", (0.46, 0.11, 0.025), C.DEPLETED_MARK)
    dust.reparentTo(holder)
    dust.setPos(-0.08, 0.18, 0.035)
    dust.setH(-12)
    _respawn_glow(holder, name, state, 0.36)


def _render_fishing_spot(holder: NodePath, name: str, tier: int) -> None:
    marker_color, ripple_color = _fishing_colors(tier)
    outer = make_ground_ring(f"{name}_water_ring_outer", 0.34, ripple_color, thickness=2.0)
    outer.reparentTo(holder)
    outer.setZ(0.034)

    inner = make_ground_ring(f"{name}_water_ring_inner", 0.20, C.WATER_RIPPLE, thickness=1.4)
    inner.reparentTo(holder)
    inner.setZ(0.038)

    body = make_box(f"{name}_fish_body", (0.25, 0.11, 0.028), marker_color)
    body.reparentTo(holder)
    body.setPos(0.0, 0.0, 0.040)
    body.setH(18)

    tail = make_box(f"{name}_fish_tail", (0.10, 0.12, 0.024), marker_color)
    tail.reparentTo(holder)
    tail.setPos(-0.17, -0.055, 0.042)
    tail.setH(48)

    wake = make_box(f"{name}_wake", (0.30, 0.025, 0.012), ripple_color)
    wake.reparentTo(holder)
    wake.setPos(0.02, 0.16, 0.038)
    wake.setH(-8)

    buoy = make_cylinder(f"{name}_buoy", 0.045, 0.09, 6, C.FISH_BUOY)
    buoy.reparentTo(holder)
    buoy.setPos(0.22, -0.14, 0.042)
    bobber_top = make_box(f"{name}_buoy_top", (0.08, 0.08, 0.025), C.WATER_SHIMMER)
    bobber_top.reparentTo(holder)
    bobber_top.setPos(0.22, -0.14, 0.13)


def _render_quiet_water(holder: NodePath, name: str, state: ResourceNodeState) -> None:
    ripple = make_ground_ring(f"{name}_quiet", 0.22, C.WATER_RIPPLE, thickness=1.2)
    ripple.reparentTo(holder)
    ripple.setZ(0.032)
    marker = make_box(f"{name}_quiet_marker", (0.18, 0.024, 0.010), C.DEPLETED_MARK)
    marker.reparentTo(holder)
    marker.setPos(0.0, 0.0, 0.034)
    marker.setH(24)
    _respawn_glow(holder, name, state, 0.25)


def _render_shop(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.66, 0.42)
    counter = make_box(f"{name}_counter", (0.86, 0.62, 0.32), C.WOOD_DARK)
    counter.reparentTo(holder)
    counter.setPos(0.0, 0.06, 0.0)

    counter_top = make_box(f"{name}_counter_top", (0.96, 0.70, 0.08), C.WOOD_LIGHT)
    counter_top.reparentTo(holder)
    counter_top.setPos(0.0, 0.06, 0.34)

    canopy = make_box(f"{name}_canopy", (1.05, 0.44, 0.10), C.CLOTH_RED)
    canopy.reparentTo(holder)
    canopy.setPos(0.0, -0.25, 0.92)
    canopy_peak = make_cone(f"{name}_canopy_peak", 0.26, 0.18, 4, C.CLOTH_RED)
    canopy_peak.reparentTo(holder)
    canopy_peak.setPos(0.0, -0.25, 0.98)
    canopy_peak.setH(45)

    for offset in (-0.40, 0.40):
        post = make_cylinder(f"{name}_post_{offset}", 0.04, 0.88, 6, C.TRUNK)
        post.reparentTo(holder)
        post.setPos(offset, -0.25, 0.04)

    _render_npc(holder, f"{name}_keeper", (0.0, -0.36, 0.0), C.PLAYER_TUNIC)
    coin = make_cylinder(f"{name}_coin", 0.07, 0.025, 10, C.GOLD)
    coin.reparentTo(holder)
    coin.setPos(-0.25, 0.02, 0.45)
    sign = make_box(f"{name}_sign", (0.30, 0.055, 0.16), C.GOLD)
    sign.reparentTo(holder)
    sign.setPos(0.28, -0.48, 0.68)


def _render_bank(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.68, 0.44)
    counter = make_box(f"{name}_counter", (0.94, 0.74, 0.40), C.STONE_DARK)
    counter.reparentTo(holder)
    counter.setPos(0.0, 0.06, 0.0)

    chest = make_box(f"{name}_chest", (0.64, 0.42, 0.34), C.WOOD)
    chest.reparentTo(holder)
    chest.setPos(0.0, 0.02, 0.40)

    trim = make_box(f"{name}_trim", (0.72, 0.48, 0.06), C.GOLD)
    trim.reparentTo(holder)
    trim.setPos(0.0, 0.02, 0.58)

    cloth = make_box(f"{name}_cloth", (1.02, 0.24, 0.08), C.CLOTH_BLUE)
    cloth.reparentTo(holder)
    cloth.setPos(0.0, -0.30, 0.86)
    arch = make_cone(f"{name}_stone_arch", 0.38, 0.24, 5, C.STONE)
    arch.reparentTo(holder)
    arch.setPos(0.0, -0.30, 0.84)
    arch.setH(18)

    lock = make_box(f"{name}_lock", (0.12, 0.05, 0.14), C.GOLD)
    lock.reparentTo(holder)
    lock.setPos(0.0, -0.22, 0.43)


def _render_cooking_range(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.54, 0.40)
    base = make_box(f"{name}_base", (0.76, 0.62, 0.42), C.STONE)
    base.reparentTo(holder)
    base.setPos(0.0, 0.02, 0.0)

    mouth = make_box(f"{name}_mouth", (0.42, 0.08, 0.18), C.OUTLINE)
    mouth.reparentTo(holder)
    mouth.setPos(0.0, -0.30, 0.12)

    fire = make_box(f"{name}_fire", (0.24, 0.04, 0.10), C.CLOTH_RED)
    fire.reparentTo(holder)
    fire.setPos(0.0, -0.35, 0.16)
    ember = make_box(f"{name}_ember", (0.16, 0.035, 0.12), C.EMBER)
    ember.reparentTo(holder)
    ember.setPos(0.0, -0.385, 0.20)

    top = make_box(f"{name}_top", (0.82, 0.68, 0.08), C.STONE_DARK)
    top.reparentTo(holder)
    top.setPos(0.0, 0.02, 0.42)

    pot = make_cylinder(f"{name}_pot", 0.22, 0.20, 8, C.OUTLINE)
    pot.reparentTo(holder)
    pot.setPos(0.0, 0.02, 0.50)
    lid = make_cone(f"{name}_pot_lid", 0.18, 0.08, 8, C.STONE_DARK)
    lid.reparentTo(holder)
    lid.setPos(0.0, 0.02, 0.70)

    chimney = make_cylinder(f"{name}_chimney", 0.10, 0.72, 7, C.OUTLINE)
    chimney.reparentTo(holder)
    chimney.setPos(0.28, 0.20, 0.44)


def _render_combat_dummy(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.42, 0.28)
    post = make_cylinder(f"{name}_post", 0.08, 0.78, 7, C.TRUNK)
    post.reparentTo(holder)
    post.setZ(0.04)

    body = make_box(f"{name}_body", (0.36, 0.18, 0.44), C.WOOD_LIGHT)
    body.reparentTo(holder)
    body.setZ(0.48)

    target = make_box(f"{name}_target", (0.24, 0.04, 0.24), C.CLOTH_RED)
    target.reparentTo(holder)
    target.setPos(0.0, -0.12, 0.58)
    crossbar = make_box(f"{name}_crossbar", (0.54, 0.08, 0.08), C.WOOD_DARK)
    crossbar.reparentTo(holder)
    crossbar.setZ(0.64)

    head = make_cylinder(f"{name}_head", 0.14, 0.16, 8, C.STUMP_TOP)
    head.reparentTo(holder)
    head.setZ(0.88)


def _render_furnace(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.58, 0.42)
    base = make_cylinder(f"{name}_base", 0.36, 0.52, 8, C.STONE_DARK)
    base.reparentTo(holder)
    base.setZ(0.02)

    firebox = make_box(f"{name}_firebox", (0.34, 0.08, 0.20), C.OUTLINE)
    firebox.reparentTo(holder)
    firebox.setPos(0.0, -0.33, 0.15)

    fire = make_box(f"{name}_fire", (0.22, 0.04, 0.12), C.CLOTH_RED)
    fire.reparentTo(holder)
    fire.setPos(0.0, -0.38, 0.18)
    core = make_box(f"{name}_ember_core", (0.14, 0.035, 0.16), C.EMBER)
    core.reparentTo(holder)
    core.setPos(0.0, -0.405, 0.20)

    chimney = make_cylinder(f"{name}_chimney", 0.16, 0.54, 8, C.STONE)
    chimney.reparentTo(holder)
    chimney.setZ(0.48)

    glow = make_ground_ring(f"{name}_glow", 0.40, C.LAMP, thickness=1.4)
    glow.reparentTo(holder)
    glow.setZ(0.035)
    vent = make_cone(f"{name}_vent", 0.19, 0.16, 8, C.ASH)
    vent.reparentTo(holder)
    vent.setZ(1.00)


def _render_anvil(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.50, 0.28)
    stump = make_cylinder(f"{name}_stump", 0.18, 0.28, 8, C.STUMP)
    stump.reparentTo(holder)
    stump.setZ(0.02)

    body = make_box(f"{name}_body", (0.46, 0.22, 0.16), C.STONE_DARK)
    body.reparentTo(holder)
    body.setZ(0.30)

    horn = make_cone(f"{name}_horn", 0.16, 0.26, 5, C.STONE)
    horn.reparentTo(holder)
    horn.setPos(0.32, 0.0, 0.34)
    horn.setH(90)

    face = make_box(f"{name}_face", (0.16, 0.20, 0.18), C.STONE)
    face.reparentTo(holder)
    face.setPos(-0.28, 0.0, 0.30)
    for index, x in enumerate((-0.10, 0.00, 0.10)):
        spark = make_box(f"{name}_spark_{index}", (0.035, 0.035, 0.08), C.SPARK)
        spark.reparentTo(holder)
        spark.setPos(x, -0.16 + index * 0.03, 0.49 + index * 0.03)
        spark.setH(index * 24)


def _render_quest_npc(holder: NodePath, name: str) -> None:
    _render_npc(holder, name, (0.0, 0.0, 0.02), C.CLOTH_BLUE)
    marker = make_ground_ring(f"{name}_quest_ring", 0.34, C.GOLD, thickness=1.4)
    marker.reparentTo(holder)
    marker.setZ(0.035)


def _render_mob(holder: NodePath, obj: WorldObject) -> None:
    _shadow(holder, f"{obj.object_id}_shadow", 0.38, 0.26)
    accent = _mob_color(obj.level)

    body = make_cylinder(f"{obj.object_id}_body", 0.18, 0.46, 8, C.STONE_DARK)
    body.reparentTo(holder)
    body.setZ(0.04)

    core = make_box(f"{obj.object_id}_core", (0.24, 0.18, 0.24), accent)
    core.reparentTo(holder)
    core.setPos(0.0, -0.02, 0.38)
    core.setH(18)

    head = make_cylinder(f"{obj.object_id}_head", 0.14, 0.16, 8, C.STONE)
    head.reparentTo(holder)
    head.setZ(0.58)

    eye = make_box(f"{obj.object_id}_eye", (0.14, 0.035, 0.04), C.GOLD)
    eye.reparentTo(holder)
    eye.setPos(0.0, -0.13, 0.66)

    shoulder = make_box(f"{obj.object_id}_shoulder", (0.42, 0.12, 0.10), accent)
    shoulder.reparentTo(holder)
    shoulder.setPos(0.0, -0.02, 0.50)
    shoulder.setH(-10)

    ring = make_ground_ring(f"{obj.object_id}_combat_ring", 0.34, accent, thickness=1.4)
    ring.reparentTo(holder)
    ring.setZ(0.034)


def _render_ground_item(holder: NodePath, obj: WorldObject) -> None:
    if obj.item_id == "coins":
        for index in range(min(3, max(1, obj.quantity))):
            coin = make_cylinder(f"{obj.object_id}_coin_{index}", 0.10, 0.025, 10, C.GOLD)
            coin.reparentTo(holder)
            coin.setPos((index - 1) * 0.07, 0.0, 0.035 + index * 0.020)
        return

    _shadow(holder, f"{obj.object_id}_shadow", 0.24, 0.16)
    pouch = make_box(f"{obj.object_id}_pouch", (0.28, 0.22, 0.15), C.WOOD_LIGHT)
    pouch.reparentTo(holder)
    pouch.setZ(0.035)
    tie = make_box(f"{obj.object_id}_tie", (0.20, 0.045, 0.04), C.WOOD_DARK)
    tie.reparentTo(holder)
    tie.setPos(0.0, -0.09, 0.17)
    glint = make_box(f"{obj.object_id}_glint", (0.08, 0.018, 0.025), C.SPARK)
    glint.reparentTo(holder)
    glint.setPos(0.06, -0.11, 0.16)
    glint.setH(20)


def _render_npc(holder: NodePath, name: str, pos: tuple[float, float, float], tunic: Color) -> None:
    body = make_cylinder(f"{name}_body", 0.16, 0.54, 8, tunic)
    body.reparentTo(holder)
    body.setPos(*pos)
    head = make_cylinder(f"{name}_head", 0.16, 0.18, 8, C.SKIN)
    head.reparentTo(holder)
    head.setPos(pos[0], pos[1], pos[2] + 0.56)
    hair = make_cone(f"{name}_hair", 0.17, 0.10, 8, C.HAIR)
    hair.reparentTo(holder)
    hair.setPos(pos[0], pos[1], pos[2] + 0.74)


def _render_fence(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.52, 0.16)
    for offset in (-0.33, 0.33):
        post = make_cylinder(f"{name}_post_{offset}", 0.055, 0.42, 6, C.WOOD_DARK)
        post.reparentTo(holder)
        post.setPos(offset, 0.0, 0.02)
    for z in (0.18, 0.34):
        rail = make_box(f"{name}_rail_{z}", (0.78, 0.08, 0.07), C.WOOD)
        rail.reparentTo(holder)
        rail.setZ(z)


def _render_signpost(holder: NodePath, name: str) -> None:
    post = make_cylinder(f"{name}_post", 0.045, 0.62, 6, C.WOOD_DARK)
    post.reparentTo(holder)
    board = make_box(f"{name}_board", (0.46, 0.10, 0.18), C.WOOD_LIGHT)
    board.reparentTo(holder)
    board.setPos(0.0, -0.02, 0.52)
    cap = make_cone(f"{name}_cap", 0.09, 0.10, 5, C.WOOD)
    cap.reparentTo(holder)
    cap.setZ(0.64)


def _render_crate(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.32, 0.24)
    crate = make_box(f"{name}_crate", (0.42, 0.42, 0.34), C.WOOD)
    crate.reparentTo(holder)
    trim_a = make_box(f"{name}_trim_a", (0.48, 0.05, 0.36), C.WOOD_DARK)
    trim_a.reparentTo(holder)
    trim_a.setPos(0.0, -0.20, 0.02)
    trim_b = make_box(f"{name}_trim_b", (0.05, 0.48, 0.36), C.WOOD_DARK)
    trim_b.reparentTo(holder)
    trim_b.setPos(-0.20, 0.0, 0.02)


def _render_barrel(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.26, 0.20)
    barrel = make_cylinder(f"{name}_barrel", 0.20, 0.42, 10, C.WOOD)
    barrel.reparentTo(holder)
    for z in (0.08, 0.31):
        band = make_cylinder(f"{name}_band_{z}", 0.21, 0.025, 10, C.STONE_DARK)
        band.reparentTo(holder)
        band.setZ(z)


def _render_mushroom(holder: NodePath, name: str) -> None:
    stem = make_cylinder(f"{name}_stem", 0.04, 0.14, 6, C.STUMP_TOP)
    stem.reparentTo(holder)
    cap = make_cone(f"{name}_cap", 0.16, 0.12, 8, C.CLOTH_RED)
    cap.reparentTo(holder)
    cap.setZ(0.13)


def _render_bush(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.32, 0.22)
    for index, (x, y, radius) in enumerate(((-0.10, 0.00, 0.19), (0.10, 0.03, 0.17), (0.00, -0.10, 0.15))):
        clump = make_cone(f"{name}_clump_{index}", radius, 0.24, 7, _tree_colors(1)[index % 3])
        clump.reparentTo(holder)
        clump.setPos(x, y, 0.04)


def _render_ruins(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.42, 0.28)
    for index, (x, y, h) in enumerate(((-0.16, 0.06, 0.22), (0.08, -0.04, 0.14), (0.24, 0.12, 0.28))):
        block = make_box(f"{name}_block_{index}", (0.22, 0.18, h), C.STONE)
        block.reparentTo(holder)
        block.setPos(x, y, 0.0)
        block.setH(index * 17)


def _render_lamp(holder: NodePath, name: str) -> None:
    post = make_cylinder(f"{name}_post", 0.035, 0.70, 6, C.WOOD_DARK)
    post.reparentTo(holder)
    lantern = make_box(f"{name}_lantern", (0.18, 0.14, 0.18), C.LAMP)
    lantern.reparentTo(holder)
    lantern.setZ(0.66)
    roof = make_cone(f"{name}_roof", 0.13, 0.10, 4, C.STONE_DARK)
    roof.reparentTo(holder)
    roof.setZ(0.84)
    glow = make_ground_ring(f"{name}_glow", 0.28, C.LAMP, thickness=1.0)
    glow.reparentTo(holder)
    glow.setZ(0.025)


def _render_dock(holder: NodePath, name: str) -> None:
    for index, y in enumerate((-0.24, 0.0, 0.24)):
        plank = make_box(f"{name}_plank_{index}", (0.76, 0.16, 0.06), C.WOOD)
        plank.reparentTo(holder)
        plank.setPos(0.0, y, 0.03)
    for x in (-0.32, 0.32):
        rail = make_box(f"{name}_rail_{x}", (0.08, 0.72, 0.07), C.WOOD_DARK)
        rail.reparentTo(holder)
        rail.setPos(x, 0.0, 0.08)


def _shadow(holder: NodePath, name: str, sx: float, sy: float) -> None:
    shadow = make_box(name, (sx, sy, 0.010), C.SHADOW)
    shadow.reparentTo(holder)
    shadow.setZ(0.006)


def _respawn_glow(holder: NodePath, name: str, state: ResourceNodeState, radius: float) -> None:
    if state.respawn_at is None:
        return
    glow = make_ground_ring(f"{name}_respawn_glow", radius, C.RESPAWN_GLOW, thickness=1.8)
    glow.reparentTo(holder)
    glow.setZ(0.035)


def _palette_color(tile: Tile, palette: tuple[Color, ...]) -> Color:
    index = _hash(tile, 13) % len(palette)
    return palette[index]


def _hash(tile: Tile, salt: int) -> int:
    x, y = tile
    return (x * 37 + y * 61 + x * y * 17 + salt * 101) & 0xFFFF


def _tree_colors(level: int) -> tuple[Color, Color, Color]:
    palette: dict[int, tuple[Color, Color, Color]] = {
        1: ((0.07, 0.25, 0.11, 1.0), (0.12, 0.37, 0.16, 1.0), (0.20, 0.48, 0.22, 1.0)),
        2: ((0.10, 0.29, 0.10, 1.0), (0.19, 0.43, 0.13, 1.0), (0.36, 0.56, 0.22, 1.0)),
        3: ((0.10, 0.31, 0.20, 1.0), (0.18, 0.46, 0.30, 1.0), (0.40, 0.60, 0.42, 1.0)),
        4: ((0.24, 0.31, 0.12, 1.0), (0.42, 0.46, 0.16, 1.0), (0.65, 0.58, 0.24, 1.0)),
        5: ((0.05, 0.20, 0.14, 1.0), (0.08, 0.30, 0.22, 1.0), (0.16, 0.40, 0.32, 1.0)),
        15: ((0.12, 0.32, 0.10, 1.0), (0.20, 0.44, 0.14, 1.0), (0.34, 0.56, 0.20, 1.0)),
        30: ((0.12, 0.34, 0.20, 1.0), (0.20, 0.48, 0.30, 1.0), (0.38, 0.62, 0.42, 1.0)),
        45: ((0.26, 0.34, 0.13, 1.0), (0.43, 0.48, 0.18, 1.0), (0.64, 0.58, 0.24, 1.0)),
        60: ((0.05, 0.22, 0.14, 1.0), (0.08, 0.32, 0.22, 1.0), (0.15, 0.42, 0.31, 1.0)),
        75: ((0.10, 0.17, 0.24, 1.0), (0.18, 0.28, 0.42, 1.0), (0.42, 0.34, 0.62, 1.0)),
        90: ((0.20, 0.25, 0.20, 1.0), (0.32, 0.42, 0.30, 1.0), (0.56, 0.68, 0.48, 1.0)),
    }
    return _tiered_palette(level, palette)


def _rock_colors(level: int) -> tuple[Color, Color, Color]:
    palette: dict[int, tuple[Color, Color, Color]] = {
        1: (C.STONE_DARK, C.STONE, C.COPPER),
        2: ((0.25, 0.25, 0.27, 1.0), C.STONE_LIGHT, C.IRON),
        3: ((0.11, 0.11, 0.12, 1.0), (0.24, 0.24, 0.25, 1.0), C.COAL),
        4: ((0.18, 0.26, 0.29, 1.0), (0.34, 0.48, 0.51, 1.0), C.MITHRIL),
        5: ((0.16, 0.24, 0.18, 1.0), (0.34, 0.44, 0.34, 1.0), C.ADAMANT),
        15: ((0.25, 0.25, 0.27, 1.0), C.STONE_LIGHT, C.IRON),
        30: ((0.12, 0.12, 0.13, 1.0), (0.25, 0.25, 0.26, 1.0), C.COAL),
        55: ((0.20, 0.27, 0.29, 1.0), (0.34, 0.48, 0.51, 1.0), C.MITHRIL),
        70: ((0.18, 0.25, 0.20, 1.0), (0.34, 0.44, 0.34, 1.0), C.ADAMANT),
        85: ((0.13, 0.16, 0.22, 1.0), (0.26, 0.32, 0.42, 1.0), (0.32, 0.52, 0.88, 1.0)),
    }
    return _tiered_palette(level, palette)


def _fishing_colors(level: int) -> tuple[Color, Color]:
    palette: dict[int, tuple[Color, Color]] = {
        1: ((0.93, 0.86, 0.56, 1.0), C.WATER_RIPPLE),
        2: ((0.98, 0.62, 0.35, 1.0), (0.64, 0.82, 0.86, 1.0)),
        3: ((0.94, 0.42, 0.30, 1.0), (0.58, 0.76, 0.86, 1.0)),
        4: ((0.48, 0.26, 0.66, 1.0), (0.56, 0.72, 0.86, 1.0)),
        5: ((0.78, 0.76, 0.82, 1.0), (0.50, 0.66, 0.84, 1.0)),
        20: ((0.98, 0.62, 0.35, 1.0), (0.64, 0.82, 0.86, 1.0)),
        30: ((0.94, 0.42, 0.30, 1.0), (0.58, 0.76, 0.86, 1.0)),
        40: ((0.48, 0.26, 0.66, 1.0), (0.56, 0.72, 0.86, 1.0)),
        50: ((0.78, 0.76, 0.82, 1.0), (0.50, 0.66, 0.84, 1.0)),
        62: ((0.70, 0.60, 0.44, 1.0), (0.48, 0.64, 0.76, 1.0)),
        76: ((0.36, 0.52, 0.72, 1.0), (0.42, 0.58, 0.78, 1.0)),
        82: ((0.92, 0.78, 0.38, 1.0), (0.34, 0.52, 0.70, 1.0)),
    }
    return _tiered_palette(level, palette)


def _mob_color(level: int) -> Color:
    if level <= 1:
        return C.CLOTH_RED
    if level == 2:
        return C.COPPER
    return C.MITHRIL


def _lerp_color(a: Color, b: Color, factor: float) -> Color:
    factor = max(0.0, min(1.0, factor))
    return tuple(a[index] + (b[index] - a[index]) * factor for index in range(4))  # type: ignore[return-value]


def _tiered_palette(level: int, palette: dict[int, T]) -> T:
    selected_level = max(threshold for threshold in palette if level >= threshold)
    return palette[selected_level]
