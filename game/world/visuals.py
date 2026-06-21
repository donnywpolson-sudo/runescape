from __future__ import annotations

import math
from collections.abc import Callable
from typing import TypeVar

from panda3d.core import LineSegs, NodePath

from game import settings
from game.style import Color, WorldPalette as C
from game.systems.gathering import ResourceNode, ResourceNodeState
from game.world.grid import Tile
from game.world.objects import WorldObject, make_box, make_cone, make_cylinder, make_quad

T = TypeVar("T")
AssetRenderer = Callable[[NodePath, WorldObject, ResourceNode | None, ResourceNodeState, int], None]
# Optional imported model renderers can be registered per render kind later.
# Procedural renderers below remain the fallback for every object kind.
ASSET_RENDERERS: dict[str, AssetRenderer] = {}


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
    _shadow(holder, f"{name}_shadow", 0.64, 0.42)

    base = make_box(f"{name}_base", (0.74, 0.62, 0.30), C.STONE_DARK)
    base.reparentTo(holder)
    base.setH(18)

    crest = make_cone(f"{name}_crest", 0.46, 0.42, 5, C.STONE)
    crest.reparentTo(holder)
    crest.setZ(0.26)
    crest.setH(-12)

    chip = make_box(f"{name}_chip", (0.22, 0.18, 0.10), C.STONE_LIGHT)
    chip.reparentTo(holder)
    chip.setPos(0.25, -0.18, 0.05)
    chip.setH(28)

    side = make_box(f"{name}_side_slab", (0.24, 0.42, 0.18), C.STONE)
    side.reparentTo(holder)
    side.setPos(-0.28, 0.12, 0.06)
    side.setH(-24)

    moss = make_box(f"{name}_moss", (0.30, 0.07, 0.035), C.GRASS_DARK)
    moss.reparentTo(holder)
    moss.setPos(0.04, -0.32, 0.30)
    moss.setH(10)


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

    if _render_asset_override(holder, obj, resource_node, resource_state, render_kind, tier):
        return

    if resource_node is not None and not resource_state.depleted:
        ring = make_ground_ring(f"{obj.object_id}_ready_ring", 0.43, C.RESOURCE_RING, thickness=1.4)
        ring.reparentTo(holder)
        ring.setZ(0.035)

    if render_kind == "tree":
        _render_tree(holder, obj.object_id, tier)
    elif render_kind == "stump":
        _render_stump(holder, obj.object_id, resource_state)
    elif render_kind == "ore_rock":
        _render_ore_rock(holder, obj.object_id, tier, resource_node)
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


def register_asset_renderer(render_kind: str, renderer: AssetRenderer | None) -> None:
    if renderer is None:
        ASSET_RENDERERS.pop(render_kind, None)
        return
    ASSET_RENDERERS[render_kind] = renderer


def _render_asset_override(
    holder: NodePath,
    obj: WorldObject,
    resource_node: ResourceNode | None,
    resource_state: ResourceNodeState,
    render_kind: str,
    tier: int,
) -> bool:
    renderer = ASSET_RENDERERS.get(render_kind)
    if renderer is None:
        return False
    renderer(holder, obj, resource_node, resource_state, tier)
    return True


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
    _shadow(parent, "player_shadow", 0.40, 0.26)

    for side, x in (("left", -0.09), ("right", 0.09)):
        leg = parent.attachNewNode(f"player_{side}_leg")
        leg.setPos(x, 0.0, 0.40)
        thigh = make_box(f"player_{side}_trouser", (0.12, 0.13, 0.35), C.PLAYER_TROUSERS)
        thigh.reparentTo(leg)
        thigh.setPos(0.0, 0.0, -0.34)
        boot = make_box(f"player_{side}_boot", (0.16, 0.22, 0.10), C.PLAYER_BOOT)
        boot.reparentTo(leg)
        boot.setPos(0.0, -0.03, -0.44)
        boot.setH(-8 if side == "left" else 8)
        kneepad = make_box(f"player_{side}_knee", (0.13, 0.04, 0.08), C.LEATHER)
        kneepad.reparentTo(leg)
        kneepad.setPos(0.0, -0.075, -0.19)
        parts[f"{side}_leg"] = leg
        parts[f"{side}_boot"] = boot

    body = parent.attachNewNode("player_body")
    body.setZ(0.40)
    torso = make_box("player_torso", (0.40, 0.28, 0.43), C.PLAYER_TUNIC)
    torso.reparentTo(body)
    skirt = make_box("player_tunic_skirt", (0.46, 0.30, 0.13), C.PLAYER_SLEEVE)
    skirt.reparentTo(body)
    skirt.setPos(0.0, 0.0, -0.06)
    chest = make_box("player_chest_highlight", (0.24, 0.035, 0.22), C.CLOTH_BLUE)
    chest.reparentTo(body)
    chest.setPos(0.0, -0.16, 0.20)
    collar = make_box("player_collar", (0.30, 0.30, 0.055), C.CLOTH_CREAM)
    collar.reparentTo(body)
    collar.setZ(0.42)
    belt = make_box("player_belt", (0.44, 0.31, 0.06), C.LEATHER)
    belt.reparentTo(body)
    belt.setZ(0.08)
    buckle = make_box("player_buckle", (0.11, 0.035, 0.08), C.GOLD)
    buckle.reparentTo(body)
    buckle.setPos(0.0, -0.17, 0.10)
    parts["body"] = body

    shoulders = make_box("player_shoulders", (0.56, 0.20, 0.09), C.PLAYER_SLEEVE)
    shoulders.reparentTo(parent)
    shoulders.setZ(0.79)

    for side, x, roll in (("left", -0.28, -5.0), ("right", 0.28, 5.0)):
        arm = parent.attachNewNode(f"player_{side}_arm")
        arm.setPos(x, -0.01, 0.76)
        arm.setR(roll)
        sleeve = make_box(f"player_{side}_sleeve", (0.105, 0.12, 0.30), C.PLAYER_SLEEVE)
        sleeve.reparentTo(arm)
        sleeve.setPos(0.0, 0.0, -0.28)
        cuff = make_box(f"player_{side}_cuff", (0.115, 0.13, 0.05), C.CLOTH_CREAM)
        cuff.reparentTo(arm)
        cuff.setPos(0.0, 0.0, -0.31)
        hand = make_cylinder(f"player_{side}_hand", 0.060, 0.070, 7, C.SKIN)
        hand.reparentTo(arm)
        hand.setPos(0.0, -0.01, -0.39)
        parts[f"{side}_arm"] = arm

    tool = parent.attachNewNode("player_tool")
    tool.setPos(0.33, -0.07, 0.37)
    tool.setHpr(-16, 0, -10)
    handle = make_box("player_tool_handle", (0.045, 0.055, 0.50), C.WOOD_LIGHT)
    handle.reparentTo(tool)
    head = make_box("player_tool_head", (0.18, 0.070, 0.09), C.METAL_LIGHT)
    head.reparentTo(tool)
    head.setPos(-0.05, -0.005, 0.44)
    edge = make_box("player_tool_edge", (0.07, 0.080, 0.11), C.METAL_DARK)
    edge.reparentTo(tool)
    edge.setPos(-0.14, -0.006, 0.42)
    parts["tool"] = tool

    shield = make_box("player_backpack_shield", (0.26, 0.06, 0.34), C.LEATHER)
    shield.reparentTo(parent)
    shield.setPos(-0.24, 0.14, 0.55)
    shield.setH(12)
    shield_boss = make_box("player_shield_boss", (0.10, 0.035, 0.10), C.METAL)
    shield_boss.reparentTo(parent)
    shield_boss.setPos(-0.24, 0.10, 0.68)
    shield_boss.setH(12)

    neck = make_cylinder("player_neck", 0.075, 0.10, 8, C.SKIN_DARK)
    neck.reparentTo(parent)
    neck.setZ(0.78)
    head = parent.attachNewNode("player_head")
    head.setZ(0.88)
    skull = make_cylinder("player_skull", 0.16, 0.20, 9, C.SKIN)
    skull.reparentTo(head)
    hair = make_cone("player_hair", 0.18, 0.13, 9, C.HAIR)
    hair.reparentTo(head)
    hair.setZ(0.18)
    hair_fringe = make_box("player_hair_fringe", (0.22, 0.055, 0.055), C.HAIR)
    hair_fringe.reparentTo(head)
    hair_fringe.setPos(0.0, -0.13, 0.17)
    nose = make_box("player_nose", (0.050, 0.085, 0.045), C.SKIN_DARK)
    nose.reparentTo(head)
    nose.setPos(0.0, -0.15, 0.10)
    for index, x in enumerate((-0.055, 0.055)):
        eye = make_box(f"player_eye_{index}", (0.027, 0.026, 0.020), C.OUTLINE)
        eye.reparentTo(head)
        eye.setPos(x, -0.145, 0.13)
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
    base = make_quad("grass_base", settings.TILE_SIZE, _grass_base_color(tile))
    base.reparentTo(holder)


def _render_dirt_tile(holder: NodePath, tile: Tile, edge_dirs: set[str]) -> None:
    base = make_quad("dirt_base", settings.TILE_SIZE, C.SHORE)
    base.reparentTo(holder)

    path = make_box("dirt_path", (0.92, 0.92, 0.018), _palette_color(tile, C.DIRT))
    path.reparentTo(holder)
    path.setPos(0.50, 0.50, 0.0)

    for edge in edge_dirs:
        if edge in {"west", "east"}:
            strip = make_box(f"dirt_edge_{edge}", (0.08, 1.0, 0.024), C.DIRT_EDGE)
            strip.setPos(0.04 if edge == "west" else 0.96, 0.50, 0.006)
        else:
            strip = make_box(f"dirt_edge_{edge}", (1.0, 0.08, 0.024), C.DIRT_EDGE)
            strip.setPos(0.50, 0.04 if edge == "south" else 0.96, 0.006)
        strip.reparentTo(holder)


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
    if _hash(tile, 9) == 0:
        ripple = make_box("water_long_ripple", (0.54, 0.022, 0.010), C.WATER_RIPPLE)
        ripple.reparentTo(holder)
        ripple.setPos(0.42, 0.72, 0.014)
        ripple.setH(-8)

    for edge in edge_dirs:
        if edge in {"west", "east"}:
            strip = make_box(f"shore_{edge}", (0.05, 1.0, 0.012), C.SHORE)
            strip.setPos(0.025 if edge == "west" else 0.975, 0.50, 0.018)
        else:
            strip = make_box(f"shore_{edge}", (1.0, 0.05, 0.012), C.SHORE)
            strip.setPos(0.50, 0.025 if edge == "south" else 0.975, 0.018)
        strip.reparentTo(holder)
        if edge in {"west", "east"}:
            foam = make_box(f"shore_foam_{edge}", (0.035, 0.62, 0.010), C.WATER_SHIMMER)
            foam.setPos(0.065 if edge == "west" else 0.935, 0.50, 0.026)
        else:
            foam = make_box(f"shore_foam_{edge}", (0.62, 0.035, 0.010), C.WATER_SHIMMER)
            foam.setPos(0.50, 0.065 if edge == "south" else 0.935, 0.026)
        foam.reparentTo(holder)


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
    branch_tip = make_box(f"{name}_branch_tip", (0.08, 0.28, 0.06), C.TRUNK)
    branch_tip.reparentTo(holder)
    branch_tip.setPos(-0.12, 0.10, 0.78)
    branch_tip.setH(42)

    bark_mark = make_box(f"{name}_bark_mark", (0.055, 0.035, 0.34), C.BARK_HIGHLIGHT)
    bark_mark.reparentTo(holder)
    bark_mark.setPos(0.09, -0.11, 0.32)
    bark_mark.setH(8)
    knot = make_box(f"{name}_trunk_knot", (0.065, 0.030, 0.060), C.TRUNK_DARK)
    knot.reparentTo(holder)
    knot.setPos(-0.07, -0.12, 0.54)
    knot.setH(-10)
    chop_mark = make_box(f"{name}_chop_mark", (0.11, 0.025, 0.10), C.STUMP_TOP)
    chop_mark.reparentTo(holder)
    chop_mark.setPos(-0.08, -0.13, 0.38)
    chop_mark.setH(-12)
    for index, (x, y, h) in enumerate(((-0.13, 0.08, -24), (0.15, 0.05, 30), (0.03, -0.14, 8))):
        root = make_box(f"{name}_root_{index}", (0.22, 0.07, 0.06), C.TRUNK_DARK)
        root.reparentTo(holder)
        root.setPos(x, y, 0.05)
        root.setH(h)

    lower = make_cone(f"{name}_leaves_lower", 0.66, 0.62, 7, leaf_dark)
    lower.reparentTo(holder)
    lower.setZ(0.58)
    lower.setH(18)

    side = make_cone(f"{name}_leaves_side", 0.38, 0.42, 6, leaf)
    side.reparentTo(holder)
    side.setPos(-0.28, 0.12, 0.78)
    side.setH(-28)
    side_b = make_cone(f"{name}_leaves_side_b", 0.34, 0.38, 6, leaf_dark)
    side_b.reparentTo(holder)
    side_b.setPos(0.28, 0.06, 0.82)
    side_b.setH(34)

    middle = make_cone(f"{name}_leaves_middle", 0.52, 0.62, 7, leaf)
    middle.reparentTo(holder)
    middle.setZ(0.94)
    middle.setH(-10)
    shadow_band = make_box(f"{name}_canopy_shadow_band", (0.58, 0.12, 0.045), leaf_dark)
    shadow_band.reparentTo(holder)
    shadow_band.setPos(0.0, -0.31, 0.92)
    shadow_band.setH(-8)

    top = make_cone(f"{name}_leaves_top", 0.34, 0.46, 7, leaf_light)
    top.reparentTo(holder)
    top.setZ(1.30)
    top.setH(8)
    glint = make_box(f"{name}_leaf_highlight", (0.18, 0.08, 0.055), leaf_light)
    glint.reparentTo(holder)
    glint.setPos(0.18, -0.24, 1.18)
    glint.setH(-22)
    fleck = make_box(f"{name}_leaf_fleck", (0.12, 0.06, 0.045), leaf_light)
    fleck.reparentTo(holder)
    fleck.setPos(-0.22, -0.20, 1.02)
    fleck.setH(26)
    for index, (x, y, z, h) in enumerate(((0.34, -0.06, 1.00, -18), (-0.36, 0.06, 0.92, 24))):
        clump = make_cone(f"{name}_leaf_clump_{index}", 0.20, 0.20, 6, leaf)
        clump.reparentTo(holder)
        clump.setPos(x, y, z)
        clump.setH(h)


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


def _render_ore_rock(holder: NodePath, name: str, tier: int, resource_node: ResourceNode | None = None) -> None:
    rock_dark, rock_light, vein_color = _rock_colors(tier, resource_node)
    _shadow(holder, f"{name}_shadow", 0.62, 0.38)

    clusters = (
        ("core", (0.46, 0.40, 0.34), (0.00, -0.02, 0.06), -16, rock_dark),
        ("left", (0.34, 0.28, 0.24), (-0.25, 0.08, 0.05), 28, rock_light),
        ("right", (0.32, 0.30, 0.26), (0.25, 0.04, 0.05), -32, rock_dark),
        ("rear", (0.30, 0.24, 0.20), (-0.08, 0.25, 0.12), 42, rock_light),
    )
    for suffix, size, pos, heading, color in clusters:
        facet = make_cone(f"{name}_faceted_boulder_{suffix}", max(size[0], size[1]) * 0.62, size[2], 5, color)
        facet.setTag("resource_color", _color_tag(color))
        facet.reparentTo(holder)
        facet.setPos(*pos)
        facet.setH(heading)
        slab = make_box(f"{name}_stone_slab_{suffix}", size, color)
        slab.setTag("resource_color", _color_tag(color))
        slab.reparentTo(holder)
        slab.setPos(pos[0], pos[1], max(0.02, pos[2] - 0.04))
        slab.setH(heading + 18)

    vein_specs = (
        ("primary", (0.10, 0.34, 0.060), (0.04, -0.24, 0.30), 24),
        ("left", (0.08, 0.22, 0.050), (-0.24, -0.02, 0.22), -32),
        ("right", (0.07, 0.20, 0.050), (0.26, 0.06, 0.24), 44),
    )
    for suffix, size, pos, heading in vein_specs:
        vein = make_box(f"{name}_ore_vein_{suffix}", size, vein_color)
        vein.setTag("resource_color", _color_tag(vein_color))
        vein.reparentTo(holder)
        vein.setPos(*pos)
        vein.setH(heading)
    crown = make_box(f"{name}_ore_crown", (0.18, 0.12, 0.045), vein_color)
    crown.setTag("resource_color", _color_tag(vein_color))
    crown.reparentTo(holder)
    crown.setPos(-0.04, -0.06, 0.39)
    crown.setH(-18)

    for index, (x, y, h) in enumerate(((-0.32, -0.20, 15), (0.34, -0.16, -28), (0.18, 0.30, 52))):
        rubble = make_box(f"{name}_loose_rubble_{index}", (0.14, 0.10, 0.055), rock_dark if index % 2 else rock_light)
        rubble.setTag("resource_color", _color_tag(rock_dark if index % 2 else rock_light))
        rubble.reparentTo(holder)
        rubble.setPos(x, y, 0.035)
        rubble.setH(h)

    crack = make_box(f"{name}_crack", (0.42, 0.030, 0.035), C.OUTLINE)
    crack.reparentTo(holder)
    crack.setPos(-0.03, -0.27, 0.18)
    crack.setH(-20)
    glint = make_box(f"{name}_ore_glint", (0.075, 0.022, 0.040), C.SPARK)
    glint.reparentTo(holder)
    glint.setPos(0.10, -0.31, 0.37)
    glint.setH(32)
    dust = make_box(f"{name}_ground_dust", (0.62, 0.10, 0.018), C.DIRT_RUT)
    dust.reparentTo(holder)
    dust.setPos(0.02, 0.33, 0.022)
    dust.setH(8)


def _render_depleted_rock(holder: NodePath, name: str, state: ResourceNodeState) -> None:
    _shadow(holder, f"{name}_shadow", 0.46, 0.28)
    rock = make_box(f"{name}_depleted_collapsed_core", (0.58, 0.46, 0.18), C.STONE_DARK)
    rock.reparentTo(holder)
    rock.setH(-18)
    for index, (x, y, h) in enumerate(((-0.20, 0.10, 28), (0.18, -0.12, -22), (0.04, 0.24, 48))):
        chip = make_box(f"{name}_depleted_rubble_{index}", (0.22, 0.13, 0.070), C.STONE)
        chip.reparentTo(holder)
        chip.setPos(x, y, 0.11)
        chip.setH(h)
    hollow = make_box(f"{name}_depleted_hollow", (0.30, 0.085, 0.055), C.OUTLINE)
    hollow.reparentTo(holder)
    hollow.setPos(-0.08, -0.22, 0.15)
    hollow.setH(-12)
    dust = make_box(f"{name}_depleted_dust", (0.58, 0.13, 0.025), C.DEPLETED_MARK)
    dust.reparentTo(holder)
    dust.setPos(-0.08, 0.18, 0.035)
    dust.setH(-12)
    _respawn_glow(holder, name, state, 0.36)


def _render_fishing_spot(holder: NodePath, name: str, tier: int) -> None:
    _marker_color, ripple_color = _fishing_colors(1)
    outer = make_ground_ring(f"{name}_water_ring_outer", 0.34, ripple_color, thickness=2.0)
    outer.reparentTo(holder)
    outer.setZ(0.034)

    inner = make_ground_ring(f"{name}_water_ring_inner", 0.20, C.WATER_RIPPLE, thickness=1.4)
    inner.reparentTo(holder)
    inner.setZ(0.038)

    net_hoop = make_ground_ring(f"{name}_net_hoop", 0.16, C.WATER_SHIMMER, thickness=1.4)
    net_hoop.reparentTo(holder)
    net_hoop.setPos(-0.04, -0.02, 0.046)
    net_handle = make_box(f"{name}_net_handle", (0.32, 0.030, 0.018), C.WOOD_LIGHT)
    net_handle.reparentTo(holder)
    net_handle.setPos(-0.18, -0.14, 0.050)
    net_handle.setH(34)
    net_cross_a = make_box(f"{name}_net_cross_a", (0.18, 0.014, 0.010), C.WATER_SHIMMER)
    net_cross_a.reparentTo(holder)
    net_cross_a.setPos(-0.04, -0.02, 0.052)
    net_cross_a.setH(28)
    net_cross_b = make_box(f"{name}_net_cross_b", (0.18, 0.014, 0.010), C.WATER_SHIMMER)
    net_cross_b.reparentTo(holder)
    net_cross_b.setPos(-0.04, -0.02, 0.053)
    net_cross_b.setH(-28)

    wake = make_box(f"{name}_wake", (0.30, 0.025, 0.012), ripple_color)
    wake.reparentTo(holder)
    wake.setPos(0.02, 0.16, 0.038)
    wake.setH(-8)
    splash = make_box(f"{name}_splash", (0.08, 0.022, 0.065), C.WATER_SHIMMER)
    splash.reparentTo(holder)
    splash.setPos(-0.06, 0.04, 0.060)
    splash.setH(16)
    far_wake = make_box(f"{name}_far_wake", (0.22, 0.018, 0.010), ripple_color)
    far_wake.reparentTo(holder)
    far_wake.setPos(-0.20, -0.12, 0.039)
    far_wake.setH(28)
    near_splash = make_box(f"{name}_near_splash", (0.040, 0.018, 0.085), C.WATER_SHIMMER)
    near_splash.reparentTo(holder)
    near_splash.setPos(0.12, -0.02, 0.070)
    near_splash.setH(-10)

    buoy = make_cylinder(f"{name}_buoy", 0.045, 0.09, 6, C.FISH_BUOY)
    buoy.reparentTo(holder)
    buoy.setPos(0.22, -0.14, 0.042)
    bobber_top = make_box(f"{name}_buoy_top", (0.08, 0.08, 0.025), C.WATER_SHIMMER)
    bobber_top.reparentTo(holder)
    bobber_top.setPos(0.22, -0.14, 0.13)
    line = make_box(f"{name}_fishing_line", (0.22, 0.012, 0.010), C.WATER_SHIMMER)
    line.reparentTo(holder)
    line.setPos(0.06, -0.08, 0.070)
    line.setH(18)
    for index, x in enumerate((-0.31, -0.25, 0.30)):
        reed = make_box(f"{name}_reed_{index}", (0.025, 0.035, 0.18 + index * 0.025), C.REED)
        reed.reparentTo(holder)
        reed.setPos(x, 0.20 - index * 0.09, 0.035)
        reed.setH(-18 + index * 16)
    for index, (x, y, h) in enumerate(((0.33, 0.12, 18), (-0.34, -0.18, -28))):
        ripple = make_box(f"{name}_edge_ripple_{index}", (0.20, 0.014, 0.010), ripple_color)
        ripple.reparentTo(holder)
        ripple.setPos(x, y, 0.041)
        ripple.setH(h)


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
    canopy_trim = make_box(f"{name}_canopy_trim", (1.10, 0.06, 0.08), C.CLOTH_CREAM)
    canopy_trim.reparentTo(holder)
    canopy_trim.setPos(0.0, -0.48, 0.88)
    for index, x in enumerate((-0.36, -0.12, 0.12, 0.36)):
        stripe = make_box(f"{name}_canopy_stripe_{index}", (0.13, 0.46, 0.105), C.CLOTH_CREAM if index % 2 == 0 else C.CLOTH_RED)
        stripe.reparentTo(holder)
        stripe.setPos(x, -0.25, 0.925)
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
    crate = make_box(f"{name}_display_crate", (0.24, 0.20, 0.16), C.WOOD)
    crate.reparentTo(holder)
    crate.setPos(0.05, 0.18, 0.44)
    shelf = make_box(f"{name}_display_shelf", (0.78, 0.08, 0.06), C.WOOD_LIGHT)
    shelf.reparentTo(holder)
    shelf.setPos(0.0, -0.14, 0.53)
    for index, x in enumerate((-0.22, -0.04, 0.16)):
        parcel = make_box(f"{name}_stock_parcel_{index}", (0.12, 0.10, 0.09), C.STUMP_TOP if index != 1 else C.METAL_LIGHT)
        parcel.reparentTo(holder)
        parcel.setPos(x, -0.14, 0.59)
    sign = make_box(f"{name}_sign", (0.30, 0.055, 0.16), C.GOLD)
    sign.reparentTo(holder)
    sign.setPos(0.28, -0.48, 0.68)
    mark = make_box(f"{name}_sign_mark", (0.10, 0.030, 0.05), C.OUTLINE)
    mark.reparentTo(holder)
    mark.setPos(0.28, -0.52, 0.73)


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
    lid = make_box(f"{name}_chest_lid", (0.68, 0.46, 0.09), C.WOOD_DARK)
    lid.reparentTo(holder)
    lid.setPos(0.0, 0.02, 0.70)

    cloth = make_box(f"{name}_cloth", (1.02, 0.24, 0.08), C.CLOTH_BLUE)
    cloth.reparentTo(holder)
    cloth.setPos(0.0, -0.30, 0.86)
    cloth_trim = make_box(f"{name}_cloth_trim", (1.06, 0.055, 0.055), C.GOLD)
    cloth_trim.reparentTo(holder)
    cloth_trim.setPos(0.0, -0.43, 0.84)
    arch = make_cone(f"{name}_stone_arch", 0.38, 0.24, 5, C.STONE)
    arch.reparentTo(holder)
    arch.setPos(0.0, -0.30, 0.84)
    arch.setH(18)

    lock = make_box(f"{name}_lock", (0.12, 0.05, 0.14), C.GOLD)
    lock.reparentTo(holder)
    lock.setPos(0.0, -0.22, 0.43)
    keyhole = make_box(f"{name}_keyhole", (0.035, 0.020, 0.055), C.OUTLINE)
    keyhole.reparentTo(holder)
    keyhole.setPos(0.0, -0.255, 0.47)
    teller_grill = make_box(f"{name}_teller_grill", (0.66, 0.030, 0.24), C.METAL_DARK)
    teller_grill.reparentTo(holder)
    teller_grill.setPos(0.0, -0.34, 0.84)
    for index, x in enumerate((-0.24, -0.08, 0.08, 0.24)):
        bar = make_box(f"{name}_teller_bar_{index}", (0.030, 0.040, 0.28), C.METAL_LIGHT)
        bar.reparentTo(holder)
        bar.setPos(x, -0.36, 0.81)
    ledger = make_box(f"{name}_ledger", (0.26, 0.18, 0.035), C.CLOTH_CREAM)
    ledger.reparentTo(holder)
    ledger.setPos(-0.28, -0.10, 0.48)
    ledger.setH(-12)
    for index in range(3):
        coin_stack = make_cylinder(f"{name}_coin_stack_{index}", 0.045, 0.030 + index * 0.012, 10, C.GOLD)
        coin_stack.reparentTo(holder)
        coin_stack.setPos(0.24 + index * 0.055, -0.11, 0.46)


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
    coal = make_box(f"{name}_coal", (0.18, 0.04, 0.045), C.ASH)
    coal.reparentTo(holder)
    coal.setPos(0.0, -0.39, 0.11)

    top = make_box(f"{name}_top", (0.82, 0.68, 0.08), C.STONE_DARK)
    top.reparentTo(holder)
    top.setPos(0.0, 0.02, 0.42)
    for index, x in enumerate((-0.30, 0.30)):
        side_brick = make_box(f"{name}_side_brick_{index}", (0.12, 0.10, 0.09), C.STONE_LIGHT)
        side_brick.reparentTo(holder)
        side_brick.setPos(x, -0.22, 0.27)

    pot = make_cylinder(f"{name}_pot", 0.22, 0.20, 8, C.OUTLINE)
    pot.reparentTo(holder)
    pot.setPos(0.0, 0.02, 0.50)
    lid = make_cone(f"{name}_pot_lid", 0.18, 0.08, 8, C.STONE_DARK)
    lid.reparentTo(holder)
    lid.setPos(0.0, 0.02, 0.70)
    spoon = make_box(f"{name}_wooden_spoon", (0.34, 0.030, 0.025), C.WOOD_LIGHT)
    spoon.reparentTo(holder)
    spoon.setPos(-0.18, 0.17, 0.63)
    spoon.setH(42)
    handle = make_cylinder(f"{name}_pan_handle", 0.025, 0.24, 6, C.METAL_DARK)
    handle.reparentTo(holder)
    handle.setPos(0.30, 0.03, 0.58)
    handle.setH(90)

    chimney = make_cylinder(f"{name}_chimney", 0.10, 0.72, 7, C.OUTLINE)
    chimney.reparentTo(holder)
    chimney.setPos(0.28, 0.20, 0.44)
    for index, (x, z) in enumerate(((0.22, 1.08), (0.32, 1.22))):
        smoke = make_cylinder(f"{name}_smoke_{index}", 0.055 + index * 0.018, 0.025, 7, C.SMOKE)
        smoke.reparentTo(holder)
        smoke.setPos(x, 0.20, z)


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
    target_center = make_box(f"{name}_target_center", (0.10, 0.035, 0.10), C.CLOTH_CREAM)
    target_center.reparentTo(holder)
    target_center.setPos(0.0, -0.145, 0.65)
    crossbar = make_box(f"{name}_crossbar", (0.54, 0.08, 0.08), C.WOOD_DARK)
    crossbar.reparentTo(holder)
    crossbar.setZ(0.64)

    head = make_cylinder(f"{name}_head", 0.14, 0.16, 8, C.STUMP_TOP)
    head.reparentTo(holder)
    head.setZ(0.88)
    face = make_box(f"{name}_face", (0.13, 0.025, 0.04), C.OUTLINE)
    face.reparentTo(holder)
    face.setPos(0.0, -0.13, 0.95)


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
    band = make_cylinder(f"{name}_iron_band", 0.37, 0.035, 8, C.METAL_DARK)
    band.reparentTo(holder)
    band.setZ(0.46)
    for index, z in enumerate((0.18, 0.34, 0.64)):
        rivet = make_cylinder(f"{name}_rivet_ring_{index}", 0.38, 0.018, 8, C.METAL_LIGHT)
        rivet.reparentTo(holder)
        rivet.setZ(z)

    glow = make_ground_ring(f"{name}_glow", 0.40, C.LAMP, thickness=1.4)
    glow.reparentTo(holder)
    glow.setZ(0.035)
    vent = make_cone(f"{name}_vent", 0.19, 0.16, 8, C.ASH)
    vent.reparentTo(holder)
    vent.setZ(1.00)
    ore = make_box(f"{name}_heated_ore", (0.13, 0.10, 0.07), C.COPPER)
    ore.reparentTo(holder)
    ore.setPos(-0.18, -0.25, 0.24)
    ore.setH(24)
    for index, (x, y, z) in enumerate(((-0.06, 0.02, 1.16), (0.05, 0.00, 1.25), (0.0, 0.04, 1.34))):
        smoke = make_cylinder(f"{name}_smoke_{index}", 0.06 + index * 0.018, 0.025, 7, C.SMOKE)
        smoke.reparentTo(holder)
        smoke.setPos(x, y, z)


def _render_anvil(holder: NodePath, name: str) -> None:
    _shadow(holder, f"{name}_shadow", 0.50, 0.28)
    stump = make_cylinder(f"{name}_stump", 0.18, 0.28, 8, C.STUMP)
    stump.reparentTo(holder)
    stump.setZ(0.02)

    body = make_box(f"{name}_body", (0.46, 0.22, 0.16), C.STONE_DARK)
    body.reparentTo(holder)
    body.setZ(0.30)
    plate = make_box(f"{name}_plate", (0.38, 0.18, 0.035), C.STONE_LIGHT)
    plate.reparentTo(holder)
    plate.setZ(0.46)
    edge = make_box(f"{name}_bright_edge", (0.42, 0.045, 0.040), C.METAL_LIGHT)
    edge.reparentTo(holder)
    edge.setPos(0.0, -0.10, 0.48)

    horn = make_cone(f"{name}_horn", 0.16, 0.26, 5, C.STONE)
    horn.reparentTo(holder)
    horn.setPos(0.32, 0.0, 0.34)
    horn.setH(90)
    hardy = make_box(f"{name}_hardy_hole", (0.070, 0.060, 0.020), C.OUTLINE)
    hardy.reparentTo(holder)
    hardy.setPos(0.12, -0.04, 0.49)

    face = make_box(f"{name}_face", (0.16, 0.20, 0.18), C.STONE)
    face.reparentTo(holder)
    face.setPos(-0.28, 0.0, 0.30)
    hammer_handle = make_box(f"{name}_hammer_handle", (0.28, 0.035, 0.035), C.WOOD_LIGHT)
    hammer_handle.reparentTo(holder)
    hammer_handle.setPos(-0.18, -0.20, 0.48)
    hammer_handle.setH(-28)
    hammer_head = make_box(f"{name}_hammer_head", (0.11, 0.075, 0.070), C.METAL_LIGHT)
    hammer_head.reparentTo(holder)
    hammer_head.setPos(-0.30, -0.15, 0.50)
    hammer_head.setH(-28)
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
    _shadow(holder, f"{obj.object_id}_shadow", 0.46, 0.30)
    accent = _mob_color(obj.level)

    body = make_cylinder(f"{obj.object_id}_body", 0.20, 0.50, 8, C.STONE_DARK)
    body.reparentTo(holder)
    body.setZ(0.04)

    core = make_box(f"{obj.object_id}_core", (0.28, 0.20, 0.28), accent)
    core.reparentTo(holder)
    core.setPos(0.0, -0.02, 0.39)
    core.setH(18)

    ribs = make_box(f"{obj.object_id}_ribs", (0.30, 0.045, 0.20), C.METAL_DARK)
    ribs.reparentTo(holder)
    ribs.setPos(0.0, -0.14, 0.44)

    head = make_cylinder(f"{obj.object_id}_head", 0.15, 0.17, 8, C.STONE)
    head.reparentTo(holder)
    head.setZ(0.62)

    for index, x in enumerate((-0.045, 0.045)):
        eye = make_box(f"{obj.object_id}_eye_{index}", (0.040, 0.030, 0.035), C.GOLD)
        eye.reparentTo(holder)
        eye.setPos(x, -0.13, 0.71)

    shoulder = make_box(f"{obj.object_id}_shoulder", (0.42, 0.12, 0.10), accent)
    shoulder.reparentTo(holder)
    shoulder.setPos(0.0, -0.02, 0.50)
    shoulder.setH(-10)

    for index, x in enumerate((-0.26, 0.26)):
        arm = make_box(f"{obj.object_id}_arm_{index}", (0.09, 0.10, 0.30), C.STONE)
        arm.reparentTo(holder)
        arm.setPos(x, -0.02, 0.34)
        arm.setR(-14 if index == 0 else 14)
        hand = make_box(f"{obj.object_id}_hand_{index}", (0.105, 0.12, 0.07), C.STONE_DARK)
        hand.reparentTo(holder)
        hand.setPos(x * 1.06, -0.04, 0.29)

    for index, x in enumerate((-0.13, 0.13)):
        foot = make_box(f"{obj.object_id}_foot_{index}", (0.16, 0.20, 0.08), C.STONE_DARK)
        foot.reparentTo(holder)
        foot.setPos(x, -0.02, 0.02)
        foot.setH(10 if index == 0 else -10)

    ring = make_ground_ring(f"{obj.object_id}_combat_ring", 0.34, accent, thickness=1.4)
    ring.reparentTo(holder)
    ring.setZ(0.034)
    max_hitpoints = max(1, obj.max_hitpoints or obj.hitpoints)
    ratio = max(0.0, min(1.0, obj.hitpoints / max_hitpoints))
    hp_back = make_box(f"{obj.object_id}_hp_bar_back", (0.46, 0.040, 0.050), C.OUTLINE)
    hp_back.reparentTo(holder)
    hp_back.setPos(0.0, -0.23, 0.84)
    fill_color = C.CLOTH_GREEN if ratio > 0.55 else C.GOLD if ratio > 0.25 else C.CLOTH_RED
    hp_fill = make_box(f"{obj.object_id}_hp_bar_fill", (0.42, 0.026, 0.055), fill_color)
    hp_fill.reparentTo(holder)
    hp_fill.setScale(max(0.001, ratio), 1.0, 1.0)
    hp_fill.setPos(-0.21 * (1.0 - ratio), -0.23, 0.855)


def _render_ground_item(holder: NodePath, obj: WorldObject) -> None:
    if obj.item_id == "coins":
        _shadow(holder, f"{obj.object_id}_shadow", 0.22, 0.14)
        for index in range(min(3, max(1, obj.quantity))):
            coin = make_cylinder(f"{obj.object_id}_coin_{index}", 0.10, 0.025, 10, C.GOLD)
            coin.reparentTo(holder)
            coin.setPos((index - 1) * 0.07, 0.0, 0.035 + index * 0.020)
        sparkle = make_box(f"{obj.object_id}_sparkle", (0.05, 0.014, 0.035), C.SPARK)
        sparkle.reparentTo(holder)
        sparkle.setPos(0.11, -0.07, 0.12)
        sparkle.setH(35)
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
    _shadow(holder, f"{name}_shadow", 0.34, 0.22)
    body = make_box(f"{name}_body", (0.34, 0.24, 0.48), tunic)
    body.reparentTo(holder)
    body.setPos(*pos)
    vest = make_box(f"{name}_vest", (0.24, 0.035, 0.34), C.CLOTH_CREAM)
    vest.reparentTo(holder)
    vest.setPos(pos[0], pos[1] - 0.13, pos[2] + 0.10)
    sash = make_box(f"{name}_sash", (0.36, 0.035, 0.055), C.GOLD)
    sash.reparentTo(holder)
    sash.setPos(pos[0], pos[1] - 0.14, pos[2] + 0.30)
    sash.setH(-12)
    belt = make_box(f"{name}_belt", (0.36, 0.26, 0.045), C.LEATHER)
    belt.reparentTo(holder)
    belt.setPos(pos[0], pos[1], pos[2] + 0.22)
    buckle = make_box(f"{name}_buckle", (0.07, 0.030, 0.055), C.GOLD)
    buckle.reparentTo(holder)
    buckle.setPos(pos[0], pos[1] - 0.14, pos[2] + 0.24)
    for side, x in (("left", -0.23), ("right", 0.23)):
        arm = make_box(f"{name}_{side}_arm", (0.08, 0.10, 0.34), tunic)
        arm.reparentTo(holder)
        arm.setPos(pos[0] + x, pos[1], pos[2] + 0.29)
        arm.setR(-7 if side == "left" else 7)
        hand = make_cylinder(f"{name}_{side}_hand", 0.050, 0.055, 7, C.SKIN)
        hand.reparentTo(holder)
        hand.setPos(pos[0] + x, pos[1] - 0.01, pos[2] + 0.24)
    for side, x in (("left", -0.08), ("right", 0.08)):
        boot = make_box(f"{name}_{side}_boot", (0.13, 0.18, 0.08), C.PLAYER_BOOT)
        boot.reparentTo(holder)
        boot.setPos(pos[0] + x, pos[1] - 0.02, pos[2])
    head = make_cylinder(f"{name}_head", 0.15, 0.18, 8, C.SKIN)
    head.reparentTo(holder)
    head.setPos(pos[0], pos[1], pos[2] + 0.55)
    hair = make_cone(f"{name}_hair", 0.17, 0.10, 8, C.HAIR)
    hair.reparentTo(holder)
    hair.setPos(pos[0], pos[1], pos[2] + 0.72)
    brow = make_box(f"{name}_brow", (0.13, 0.025, 0.025), C.HAIR)
    brow.reparentTo(holder)
    brow.setPos(pos[0], pos[1] - 0.14, pos[2] + 0.68)
    nose = make_box(f"{name}_nose", (0.045, 0.070, 0.035), C.SKIN_DARK)
    nose.reparentTo(holder)
    nose.setPos(pos[0], pos[1] - 0.14, pos[2] + 0.63)
    for index, x in enumerate((-0.050, 0.050)):
        eye = make_box(f"{name}_eye_{index}", (0.024, 0.022, 0.018), C.OUTLINE)
        eye.reparentTo(holder)
        eye.setPos(pos[0] + x, pos[1] - 0.14, pos[2] + 0.66)


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


def _grass_base_color(tile: Tile) -> Color:
    color = C.GRASS[_grass_noise(tile, 1) % len(C.GRASS)]
    region = (tile[0] // 5, tile[1] // 5)
    regional_tints = (C.GRASS_LIGHT, C.GRASS_DARK, C.GRASS_DRY, C.GRASS_SHADOW_PATCH)
    tint = regional_tints[_grass_noise(region, 2) % len(regional_tints)]
    factor = 0.07 + (_grass_noise(region, 3) % 5) * 0.01
    return _lerp_color(color, tint, factor)


def _grass_offset(tile: Tile, salt: int) -> float:
    return 0.14 + (_grass_noise(tile, salt) % 73) / 100.0


def _grass_noise(tile: Tile, salt: int) -> int:
    x, y = tile
    value = (x * 0x9E3779B1) ^ (y * 0x85EBCA77) ^ (salt * 0xC2B2AE3D)
    value ^= value >> 16
    value *= 0x7FEB352D
    value ^= value >> 15
    return value & 0xFFFF


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


def _rock_colors(level: int, resource_node: ResourceNode | None = None) -> tuple[Color, Color, Color]:
    ore_key = ""
    if resource_node is not None:
        ore_key = resource_node.item_reward or resource_node.node_type
    by_ore: dict[str, tuple[Color, Color, Color]] = {
        "copper_ore": ((0.56, 0.20, 0.08, 1.0), (0.86, 0.42, 0.18, 1.0), C.COPPER),
        "copper_rock": ((0.56, 0.20, 0.08, 1.0), (0.86, 0.42, 0.18, 1.0), C.COPPER),
        "tin_ore": ((0.42, 0.44, 0.43, 1.0), (0.70, 0.72, 0.70, 1.0), (0.60, 0.62, 0.60, 1.0)),
        "tin_rock": ((0.42, 0.44, 0.43, 1.0), (0.70, 0.72, 0.70, 1.0), (0.60, 0.62, 0.60, 1.0)),
        "iron_ore": ((0.38, 0.22, 0.12, 1.0), (0.66, 0.42, 0.22, 1.0), (0.58, 0.32, 0.15, 1.0)),
        "iron_rock": ((0.38, 0.22, 0.12, 1.0), (0.66, 0.42, 0.22, 1.0), (0.58, 0.32, 0.15, 1.0)),
        "coal": ((0.05, 0.05, 0.06, 1.0), (0.18, 0.18, 0.20, 1.0), C.COAL),
        "coal_rock": ((0.05, 0.05, 0.06, 1.0), (0.18, 0.18, 0.20, 1.0), C.COAL),
        "mithril_ore": ((0.04, 0.14, 0.34, 1.0), (0.10, 0.28, 0.62, 1.0), (0.08, 0.34, 0.78, 1.0)),
        "mithril_rock": ((0.04, 0.14, 0.34, 1.0), (0.10, 0.28, 0.62, 1.0), (0.08, 0.34, 0.78, 1.0)),
        "adamant_ore": ((0.12, 0.42, 0.18, 1.0), (0.34, 0.82, 0.38, 1.0), C.ADAMANT),
        "adamant_rock": ((0.12, 0.42, 0.18, 1.0), (0.34, 0.82, 0.38, 1.0), C.ADAMANT),
        "starsteel_ore": ((0.28, 0.56, 0.78, 1.0), (0.58, 0.84, 1.0, 1.0), (0.46, 0.74, 1.0, 1.0)),
        "starsteel_rock": ((0.28, 0.56, 0.78, 1.0), (0.58, 0.84, 1.0, 1.0), (0.46, 0.74, 1.0, 1.0)),
    }
    if ore_key in by_ore:
        return by_ore[ore_key]
    palette: dict[int, tuple[Color, Color, Color]] = {
        1: by_ore["copper_ore"],
        2: by_ore["tin_ore"],
        3: by_ore["coal"],
        4: by_ore["mithril_ore"],
        5: by_ore["adamant_ore"],
        15: by_ore["iron_ore"],
        30: by_ore["coal"],
        55: by_ore["mithril_ore"],
        70: by_ore["adamant_ore"],
        85: by_ore["starsteel_ore"],
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


def _color_tag(color: Color) -> str:
    return ",".join(f"{channel:.2f}" for channel in color)


def _tiered_palette(level: int, palette: dict[int, T]) -> T:
    selected_level = max(threshold for threshold in palette if level >= threshold)
    return palette[selected_level]
