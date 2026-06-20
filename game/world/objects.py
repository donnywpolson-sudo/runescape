from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat
from panda3d.core import GeomVertexWriter, LineSegs, NodePath

from game.world.grid import Tile

Color = tuple[float, float, float, float]


@dataclass
class WorldObject:
    object_id: str
    kind: str
    tile: Tile
    blocking: bool = True
    chopped: bool = False
    node_type: str = ""
    skill_id: str = ""
    required_level: int = 1
    xp_reward: int = 0
    item_reward: str = ""
    quantity_reward: int = 1
    depleted_state: str = "depleted"
    respawn_seconds: float | None = None
    depleted: bool = False
    node: Any = None

    @property
    def is_interactable(self) -> bool:
        return self.kind == "shop" or self.is_resource_node or self.depleted

    @property
    def is_resource_node(self) -> bool:
        return bool(self.node_type and self.skill_id and self.item_reward)

    @property
    def node_id(self) -> str:
        return self.object_id


def make_box(name: str, size: tuple[float, float, float], color: Color) -> NodePath:
    sx, sy, sz = size
    hx, hy = sx / 2.0, sy / 2.0
    vertices = [
        (-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
        (-hx, -hy, sz), (hx, -hy, sz), (hx, hy, sz), (-hx, hy, sz),
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    return _make_poly_node(name, vertices, faces, color)


def make_quad(name: str, size: float, color: Color) -> NodePath:
    vertices = [(0, 0, 0), (size, 0, 0), (size, size, 0), (0, size, 0)]
    return _make_poly_node(name, vertices, [(0, 1, 2, 3)], color)


def make_cylinder(name: str, radius: float, height: float, sides: int, color: Color) -> NodePath:
    vertices: list[tuple[float, float, float]] = []
    for z in (0.0, height):
        for index in range(sides):
            angle = math.tau * index / sides
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, z))

    bottom_center = len(vertices)
    vertices.append((0.0, 0.0, 0.0))
    top_center = len(vertices)
    vertices.append((0.0, 0.0, height))

    faces: list[tuple[int, ...]] = []
    for index in range(sides):
        nxt = (index + 1) % sides
        faces.append((index, nxt, sides + nxt, sides + index))
        faces.append((bottom_center, nxt, index))
        faces.append((top_center, sides + index, sides + nxt))
    return _make_poly_node(name, vertices, faces, color)


def make_cone(name: str, radius: float, height: float, sides: int, color: Color) -> NodePath:
    vertices: list[tuple[float, float, float]] = []
    for index in range(sides):
        angle = math.tau * index / sides
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, 0.0))
    tip = len(vertices)
    vertices.append((0.0, 0.0, height))
    center = len(vertices)
    vertices.append((0.0, 0.0, 0.0))

    faces: list[tuple[int, ...]] = []
    for index in range(sides):
        nxt = (index + 1) % sides
        faces.append((index, nxt, tip))
        faces.append((center, nxt, index))
    return _make_poly_node(name, vertices, faces, color)


def make_grid_lines(width: int, height: int, color: Color) -> NodePath:
    lines = LineSegs()
    lines.setColor(*color)
    lines.setThickness(1.0)
    z = 0.015
    for x in range(width + 1):
        lines.moveTo(x, 0, z)
        lines.drawTo(x, height, z)
    for y in range(height + 1):
        lines.moveTo(0, y, z)
        lines.drawTo(width, y, z)
    return NodePath(lines.create())


def _make_poly_node(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    color: Color,
) -> NodePath:
    fmt = GeomVertexFormat.getV3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    color_writer = GeomVertexWriter(vdata, "color")

    for vertex in vertices:
        vertex_writer.addData3f(*vertex)
        color_writer.addData4f(*color)

    tris = GeomTriangles(Geom.UHStatic)
    for face in faces:
        if len(face) == 3:
            tris.addVertices(*face)
        elif len(face) == 4:
            a, b, c, d = face
            tris.addVertices(a, b, c)
            tris.addVertices(a, c, d)
    tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    path = NodePath(node)
    path.setLightOff(1)
    return path
