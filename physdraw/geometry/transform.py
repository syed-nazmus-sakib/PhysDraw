from __future__ import annotations

import math
from dataclasses import dataclass

from .point import Point
from .vector import Vector


@dataclass(frozen=True, slots=True)
class Transform:
    """A rigid transform: rotation (counter-clockwise, degrees) followed by translation."""

    translation: Vector = Vector(0.0, 0.0)
    rotation_deg: float = 0.0

    @classmethod
    def identity(cls) -> Transform:
        return cls()

    @classmethod
    def translate(cls, v: Vector | tuple[float, float]) -> Transform:
        if not isinstance(v, Vector):
            v = Vector(*v)
        return cls(translation=v)

    def apply_point(self, p: Point) -> Point:
        r = math.radians(self.rotation_deg)
        c, s = math.cos(r), math.sin(r)
        return Point(
            p.x * c - p.y * s + self.translation.x,
            p.x * s + p.y * c + self.translation.y,
        )

    def apply_vector(self, v: Vector) -> Vector:
        r = math.radians(self.rotation_deg)
        c, s = math.cos(r), math.sin(r)
        return Vector(v.x * c - v.y * s, v.x * s + v.y * c)

    def then(self, outer: Transform) -> Transform:
        """The transform equivalent to applying self first, then `outer`."""
        t = outer.apply_vector(self.translation) + outer.translation
        return Transform(translation=t, rotation_deg=self.rotation_deg + outer.rotation_deg)
