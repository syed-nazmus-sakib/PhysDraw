from __future__ import annotations

import math
from dataclasses import dataclass

from .point import Point
from .vector import Vector


@dataclass(frozen=True, slots=True)
class Arc:
    """A circular arc in world space.

    `sweep_deg` is positive for a counter-clockwise sweep from start to end.
    """

    center: Point
    radius: float
    start_deg: float
    sweep_deg: float

    @property
    def end_deg(self) -> float:
        return self.start_deg + self.sweep_deg

    def point_at(self, degrees: float) -> Point:
        return self.center + Vector.from_polar(degrees, self.radius)

    @property
    def start_point(self) -> Point:
        return self.point_at(self.start_deg)

    @property
    def end_point(self) -> Point:
        return self.point_at(self.end_deg)

    def sample_points(self, step: float = 5.0) -> list[Point]:
        n = max(2, int(abs(self.sweep_deg) / step) + 1)
        return [self.point_at(self.start_deg + i * self.sweep_deg / (n - 1)) for i in range(n)]

    @classmethod
    def between(
        cls,
        center: Point,
        start_direction: Vector,
        end_direction: Vector,
        radius: float,
        *,
        minor: bool = True,
    ) -> Arc:
        """The arc at `center` spanning the angle from start to end direction.

        With `minor=True` (default) the arc takes the smaller angular span.
        """
        a0 = math.atan2(start_direction.y, start_direction.x)
        a1 = math.atan2(end_direction.y, end_direction.x)
        sweep = (a1 - a0) % math.tau
        if minor and sweep > math.pi:
            sweep -= math.tau
        return cls(
            center=center,
            radius=radius,
            start_deg=math.degrees(a0),
            sweep_deg=math.degrees(sweep),
        )


def external_tangents(point: Point, center: Point, radius: float) -> tuple[Point, Point]:
    """The two points where tangent lines from an external point touch a circle."""
    d = point - center
    dist = d.length
    if dist <= radius:
        raise ValueError("point must lie strictly outside the circle")
    phi = math.degrees(math.atan2(d.y, d.x))
    beta = math.degrees(math.acos(radius / dist))
    return (
        center + Vector.from_polar(phi + beta, radius),
        center + Vector.from_polar(phi - beta, radius),
    )
