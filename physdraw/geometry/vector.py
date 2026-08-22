from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Vector:
    """A free vector in world space (y points up)."""

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector) -> Vector:
        return Vector(self.x - other.x, self.y - other.y)

    def __neg__(self) -> Vector:
        return Vector(-self.x, -self.y)

    def __mul__(self, k: float) -> Vector:
        return Vector(self.x * k, self.y * k)

    __rmul__ = __mul__

    def dot(self, other: Vector) -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector) -> float:
        return self.x * other.y - self.y * other.x

    @property
    def length(self) -> float:
        return math.hypot(self.x, self.y)

    @property
    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    @property
    def angle_deg(self) -> float:
        return math.degrees(math.atan2(self.y, self.x))

    def normalized(self) -> Vector:
        n = self.length
        if n == 0.0:
            raise ValueError("cannot normalize a zero vector")
        return Vector(self.x / n, self.y / n)

    def rotated(self, degrees: float) -> Vector:
        """Rotate counter-clockwise by the given angle in degrees."""
        r = math.radians(degrees)
        c, s = math.cos(r), math.sin(r)
        return Vector(self.x * c - self.y * s, self.x * s + self.y * c)

    def perpendicular(self) -> Vector:
        """The vector rotated +90 degrees (counter-clockwise)."""
        return Vector(-self.y, self.x)

    def approx(self, other: Vector, tol: float = 1e-9) -> bool:
        return abs(self.x - other.x) <= tol and abs(self.y - other.y) <= tol

    @classmethod
    def from_polar(cls, degrees: float, length: float = 1.0) -> Vector:
        """A unit direction at `degrees` counter-clockwise from +x, scaled by length."""
        r = math.radians(degrees)
        return cls(length * math.cos(r), length * math.sin(r))


UNIT_X = Vector(1.0, 0.0)
UNIT_Y = Vector(0.0, 1.0)
