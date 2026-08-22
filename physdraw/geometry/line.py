from __future__ import annotations

import math
from dataclasses import dataclass

from .point import Point
from .vector import Vector


@dataclass(frozen=True, slots=True)
class Segment:
    """A directed straight segment between two points."""

    start: Point
    end: Point

    def __post_init__(self) -> None:
        if self.start == self.end:
            raise ValueError("segment start and end must differ")

    @property
    def vector(self) -> Vector:
        return self.end - self.start

    @property
    def length(self) -> float:
        return self.vector.length

    @property
    def unit(self) -> Vector:
        return self.vector.normalized()

    @property
    def normal(self) -> Vector:
        """Unit vector rotated +90 degrees (counter-clockwise) from the segment direction."""
        return self.unit.perpendicular()

    @property
    def midpoint(self) -> Point:
        return self.start.midpoint(self.end)

    def point_at(self, t: float) -> Point:
        """Point at fraction t of the way from start (t=0) to end (t=1)."""
        v = self.end - self.start
        return Point(self.start.x + t * v.x, self.start.y + t * v.y)

    def reversed(self) -> Segment:
        return Segment(self.end, self.start)

    def offset(self, distance: float) -> Segment:
        """A parallel segment shifted `distance` along the left-hand normal."""
        n = self.normal * distance
        return Segment(self.start + n, self.end + n)

    def projected_point(self, p: Point) -> Point:
        """Foot of the perpendicular from p onto the supporting line."""
        u = self.unit
        d = (p - self.start).dot(u)
        return self.start + u * d

    def closest_point(self, p: Point) -> Point:
        u = self.unit
        d = max(0.0, min(1.0, (p - self.start).dot(u) / self.length))
        return self.point_at(d)

    def distance_to_point(self, p: Point) -> float:
        return self.closest_point(p).distance_to(p)


@dataclass(frozen=True, slots=True)
class Line:
    """An infinite line through `point` in the direction of `direction` (need not be unit)."""

    point: Point
    direction: Vector

    def at(self, t: float) -> Point:
        return self.point + self.direction * t


@dataclass(frozen=True, slots=True)
class Ray:
    origin: Point
    direction: Vector

    def at(self, t: float) -> Point:
        return self.origin + self.direction * t


def line_line_intersection(a: Line, b: Line) -> Point | None:
    """Intersection of two infinite lines, or None if parallel."""
    d1, d2 = a.direction, b.direction
    denom = d1.cross(d2)
    if abs(denom) < 1e-12:
        return None
    dp = b.point - a.point
    t = dp.cross(d2) / denom
    return a.at(t)


def segments_intersect(s1: Segment, s2: Segment, tol: float = 1e-9) -> Point | None:
    """Intersection point of two finite segments, or None."""
    ip = line_line_intersection(
        Line(s1.start, s1.vector), Line(s2.start, s2.vector)
    )
    if ip is None:
        return None
    for s in (s1, s2):
        u = s.unit
        t = (ip - s.start).dot(u)
        if t < -tol or t > s.length + tol:
            return None
    return ip


def angle_between(u: Vector, v: Vector) -> float:
    """Unsigned angle between two vectors in degrees, in [0, 180]."""
    cos = u.dot(v) / (u.length * v.length)
    cos = max(-1.0, min(1.0, cos))
    return math.degrees(math.acos(cos))
