from __future__ import annotations

import math

from physdraw.geometry import (
    ORIGIN,
    Point,
    Segment,
    Transform,
    Vector,
    line_line_intersection,
)


def test_vector_arithmetic():
    v = Vector(3, 4)
    assert v.length == 5
    assert (v + Vector(1, 1)).x == 4
    assert (-v).y == -4
    assert (2 * v).x == 6
    assert v.normalized().length == 1


def test_vector_rotation():
    east = Vector(1, 0)
    north = east.rotated(90)
    assert north.approx(Vector(0, 1))
    back = north.rotated(-90)
    assert back.approx(east)
    assert Vector.from_polar(45).approx(Vector(math.sqrt(0.5), math.sqrt(0.5)))


def test_point_segment_ops():
    p = Point(1, 2) + Vector(1, 1)
    assert p == Point(2, 3)
    seg = Segment(Point(0, 0), Point(10, 0))
    assert seg.point_at(0.25) == Point(2.5, 0)
    assert seg.offset(2).start.y == 2
    foot = seg.projected_point(Point(4, 7))
    assert foot == Point(4, 0)
    assert seg.distance_to_point(Point(4, -3)) == 3


def test_line_intersection():
    from physdraw.geometry import Line

    ip = line_line_intersection(Line(Point(0, 0), Vector(1, 1)), Line(Point(0, 4), Vector(1, -1)))
    assert ip is not None and ip.approx(Point(2, 2))


def test_transform_roundtrip():
    t = Transform(rotation_deg=30.0, translation=Vector(5, 2))
    local = Point(1, 0)
    world = t.apply_point(local)
    assert world.approx(Point(1 * math.cos(math.radians(30)) + 5, 1 * math.sin(math.radians(30)) + 2))


def test_origin_constant():
    assert ORIGIN == Point(0, 0)
