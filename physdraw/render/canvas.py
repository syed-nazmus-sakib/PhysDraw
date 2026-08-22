from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Optional, Sequence

from ..geometry import Point, Vector


@dataclass(frozen=True)
class Seg:
    """A straight line segment."""

    p1: Point
    p2: Point
    width: float = 1.0
    color: str = "#000000"
    dash: tuple[float, ...] | None = None


@dataclass(frozen=True)
class Poly:
    """A filled and/or stroked polygon."""

    points: tuple[Point, ...]
    fill: str | None = None
    stroke: str | None = None
    width: float = 0.0
    dash: tuple[float, ...] | None = None
    close: bool = True


@dataclass(frozen=True)
class Circle:
    center: Point
    radius: float
    fill: str | None = None
    stroke: str | None = None
    width: float = 0.0


@dataclass(frozen=True)
class ArcSeg:
    """A circular arc; `sweep_deg` is positive counter-clockwise in world space."""

    center: Point
    radius: float
    start_deg: float
    sweep_deg: float
    width: float = 1.0
    color: str = "#000000"
    dash: tuple[float, ...] | None = None

    @property
    def end_deg(self) -> float:
        return self.start_deg + self.sweep_deg


@dataclass(frozen=True)
class Text:
    pos: Point
    text: str
    size: float
    color: str = "#000000"
    italic: bool = False
    bold: bool = False
    halign: str = "middle"  # "start" | "middle" | "end"
    rotation_deg: float = 0.0
    font_family: str | None = None


Primitive = Seg | Poly | Circle | ArcSeg | Text


def _arrow_head(tip: Point, direction: Vector, length: float, half_width: float) -> tuple[Point, Point]:
    back = tip - direction * length
    side = direction.perpendicular() * half_width
    return back + side, back - side


def draw_arrow(
    tail: Point,
    tip: Point,
    *,
    width: float,
    head_len: float,
    head_width: float,
    color: str,
    dash: tuple[float, ...] | None = None,
    label: Text | None = None,
) -> list[Primitive]:
    """A force-style arrow: shaft plus a solid triangular head at the tip."""
    d = (tip - tail).normalized()
    shaft_end = tip - d * (head_len * 0.55)
    wing_a, wing_b = _arrow_head(tip, d, head_len, head_width / 2.0)
    prims: list[Primitive] = [
        Seg(tail, shaft_end, width=width, color=color, dash=dash),
        Poly((tip, wing_a, wing_b), fill=color),
    ]
    if label is not None:
        prims.append(label)
    return prims


class Canvas:
    """Collects drawing primitives, tagged with the id of the object that drew them."""

    def __init__(self, default_font_family: str | None = None) -> None:
        self._items: list[tuple[Optional[str], Primitive]] = []
        self._group: Optional[str] = None
        self.default_font_family = default_font_family

    @contextmanager
    def group(self, gid: str) -> Iterator[None]:
        prev = self._group
        self._group = gid
        try:
            yield
        finally:
            self._group = prev

    def add(self, prim: Primitive) -> None:
        self._items.append((self._group, prim))

    # -- convenience emitters -------------------------------------------------

    def line(self, p1: Point, p2: Point, **kwargs) -> None:
        self.add(Seg(p1, p2, **kwargs))

    def polygon(self, points: Sequence[Point], **kwargs) -> None:
        self.add(Poly(tuple(points), **kwargs))

    def circle(self, center: Point, radius: float, **kwargs) -> None:
        self.add(Circle(center, radius, **kwargs))

    def arc(
        self,
        center: Point,
        radius: float,
        start_deg: float,
        end_deg: float,
        **kwargs,
    ) -> None:
        """Counter-clockwise from `start_deg` to `end_deg`, taking the minor span."""
        a0 = math.radians(start_deg)
        a1 = math.radians(end_deg)
        sweep = (a1 - a0) % math.tau
        if sweep > math.pi:
            sweep -= math.tau
        self.add(ArcSeg(center=center, radius=radius, start_deg=start_deg, sweep_deg=math.degrees(sweep), **kwargs))

    def text(self, pos: Point, string: str, size: float, **kwargs) -> None:
        kwargs.setdefault("font_family", self.default_font_family)
        self.add(Text(pos=pos, text=string, size=size, **kwargs))

    def arrow(self, tail: Point, tip: Point, **kwargs) -> None:
        for prim in draw_arrow(tail, tip, **kwargs):
            self.add(prim)

    # -- access ---------------------------------------------------------------

    @property
    def items(self) -> list[tuple[Optional[str], Primitive]]:
        return list(self._items)


@dataclass
class RenderedScene:
    """The flat output of a scene render, ready for any backend."""

    groups: list[tuple[Optional[str], Primitive]] = field(default_factory=list)
