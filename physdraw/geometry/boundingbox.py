from __future__ import annotations

from dataclasses import dataclass

from .point import Point


@dataclass
class BoundingBox:
    """An axis-aligned bounding box in world space."""

    min_x: float = float("inf")
    min_y: float = float("inf")
    max_x: float = float("-inf")
    max_y: float = float("-inf")

    @property
    def width(self) -> float:
        return max(0.0, self.max_x - self.min_x)

    @property
    def height(self) -> float:
        return max(0.0, self.max_y - self.min_y)

    @property
    def is_empty(self) -> bool:
        return self.min_x > self.max_x or self.min_y > self.max_y

    def include_point(self, p: Point) -> None:
        self.min_x = min(self.min_x, p.x)
        self.min_y = min(self.min_y, p.y)
        self.max_x = max(self.max_x, p.x)
        self.max_y = max(self.max_y, p.y)

    def include_box(self, other: BoundingBox) -> None:
        if other.is_empty:
            return
        self.include_point(Point(other.min_x, other.min_y))
        self.include_point(Point(other.max_x, other.max_y))

    def padded(self, margin: float) -> BoundingBox:
        if self.is_empty:
            return BoundingBox()
        return BoundingBox(
            self.min_x - margin,
            self.min_y - margin,
            self.max_x + margin,
            self.max_y + margin,
        )
