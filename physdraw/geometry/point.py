from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Union

from .vector import Vector


@dataclass(frozen=True, slots=True)
class Point:
    """A position in world space (y points up)."""

    x: float = 0.0
    y: float = 0.0

    def __add__(self, v: Vector) -> Point:
        return Point(self.x + v.x, self.y + v.y)

    def __sub__(self, other: Union[Vector, Point]):
        if isinstance(other, Vector):
            return Point(self.x - other.x, self.y - other.y)
        return Vector(self.x - other.x, self.y - other.y)

    def to_vector(self) -> Vector:
        return Vector(self.x, self.y)

    def moved(self, direction: Vector, distance: float) -> Point:
        return self + direction.normalized() * distance

    def midpoint(self, other: Point) -> Point:
        return Point((self.x + other.x) / 2.0, (self.y + other.y) / 2.0)

    def distance_to(self, other: Point) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def approx(self, other: Point, tol: float = 1e-9) -> bool:
        return abs(self.x - other.x) <= tol and abs(self.y - other.y) <= tol


ORIGIN = Point(0.0, 0.0)
