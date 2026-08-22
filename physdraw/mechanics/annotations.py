from __future__ import annotations

import math
from typing import TYPE_CHECKING, Union

from ..core.anchors import resolve_ref
from ..core.object import SceneObject
from ..geometry import Point, Segment, Vector
from ..render.canvas import Canvas

if TYPE_CHECKING:
    from ..core.scene import Scene


DirectionSpec = Union[Vector, float, int, tuple["Point", "Point"]]


def _dir_angle(spec: DirectionSpec) -> float:
    if isinstance(spec, Vector):
        return spec.angle_deg
    if isinstance(spec, (int, float)):
        return float(spec) % 360.0
    if isinstance(spec, tuple):
        a, b = spec
        return (b - a).angle_deg % 360.0
    raise TypeError(f"bad direction spec: {spec!r}")


class AngleMark(SceneObject):
    """An arc marking the angle between two directions at a vertex."""

    kind = "angle"
    z = 40

    def __init__(
        self,
        vertex,
        *,
        from_: DirectionSpec = Vector(1.0, 0.0),
        to: DirectionSpec = Vector(0.0, 1.0),
        radius: float = 1.0,
        label: str | None = None,
        color: str | None = None,
        name: str | None = None,
        scene=None,
    ) -> None:
        super().__init__(name=name, scene=scene)
        self.vertex_spec = vertex
        self.from_spec = from_
        self.to_spec = to
        self.radius = radius
        self.label_text = label
        self.color = color
        self._vertex: Point | None = None
        self._start_deg: float = 0.0
        self._sweep: float = 0.0

    def deps(self) -> list[SceneObject]:
        out = []
        for spec in (self.vertex_spec,):
            owner = getattr(spec, "owner", None)
            if isinstance(spec, tuple) and isinstance(spec[0], SceneObject):
                out.append(spec[0])
            elif owner is not None:
                out.append(owner)
        return out

    def place(self, scene: "Scene") -> None:
        v = resolve_ref(self.vertex_spec)
        a0 = _dir_angle(self.from_spec)
        a1 = _dir_angle(self.to_spec)
        sweep = (a1 - a0) % 360.0
        if sweep > 180.0:
            sweep -= 360.0
        self._vertex = v
        self._start_deg = a0
        self._sweep = sweep
        super().place(scene)

    @property
    def mid_deg(self) -> float:
        return self._start_deg + self._sweep / 2.0

    def render(self, canvas: Canvas, theme) -> None:
        color = self.color or theme.ink
        canvas.arc(
            center=self._vertex,
            radius=self.radius,
            start_deg=self._start_deg,
            end_deg=self._start_deg + self._sweep,
            width=theme.thin_stroke,
            color=color,
        )
        if self.label_text:
            pos = self._vertex + Vector.from_polar(
                self.mid_deg, self.radius + theme.label_pad * 1.6
            )
            canvas.text(
                pos,
                self.label_text,
                size=theme.font_size,
                color=color,
                italic=True,
                halign="middle",
            )


class Label(SceneObject):
    """Free text anchored to a point or another object's anchor."""

    kind = "label"
    z = 40

    def __init__(
        self,
        text: str,
        at,
        *,
        offset: Vector | tuple[float, float] = Vector(0.0, 0.0),
        halign: str | None = None,
        italic: bool = True,
        size_scale: float = 1.0,
        color: str | None = None,
        name: str | None = None,
        scene=None,
    ) -> None:
        super().__init__(name=name, scene=scene)
        self.text = text
        self.at_spec = at
        self.offset = offset
        self.halign = halign
        self.italic = italic
        self.size_scale = size_scale
        self.color = color
        self._pos: Point | None = None

    def deps(self) -> list[SceneObject]:
        owner = getattr(self.at_spec, "owner", None)
        if isinstance(self.at_spec, tuple) and isinstance(self.at_spec[0], SceneObject):
            return [self.at_spec[0]]
        return [owner] if owner is not None else []

    def place(self, scene: "Scene") -> None:
        base = resolve_ref(self.at_spec)
        off = self.offset
        if not isinstance(off, Vector):
            off = Vector(*off)
        self._pos = base + off
        super().place(scene)

    def render(self, canvas: Canvas, theme) -> None:
        canvas.text(
            self._pos,
            self.text,
            size=theme.font_size * self.size_scale,
            color=self.color or theme.ink,
            italic=self.italic,
            halign=self.halign or "middle",
        )


class Dimension(SceneObject):
    """A dimension line with arrows and witness ticks between two points."""

    kind = "dimension"
    z = 40

    def __init__(
        self,
        p1,
        p2,
        *,
        offset: float = 0.7,
        label: str | None = None,
        witness_ext: float = 0.18,
        name: str | None = None,
        scene=None,
    ) -> None:
        super().__init__(name=name, scene=scene)
        self.p1_spec = p1
        self.p2_spec = p2
        self.offset = offset
        self.label_text = label
        self.witness_ext = witness_ext
        self._seg: Segment | None = None
        self._orig: tuple[Point, Point] | None = None

    def deps(self) -> list[SceneObject]:
        out = []
        for spec in (self.p1_spec, self.p2_spec):
            if isinstance(spec, tuple) and isinstance(spec[0], SceneObject):
                out.append(spec[0])
            else:
                owner = getattr(spec, "owner", None)
                if owner is not None:
                    out.append(owner)
        return out

    def place(self, scene: "Scene") -> None:
        a = resolve_ref(self.p1_spec)
        b = resolve_ref(self.p2_spec)
        self._orig = (a, b)
        self._seg = Segment(a, b).offset(self.offset)
        super().place(scene)

    def render(self, canvas: Canvas, theme) -> None:
        seg = self._seg
        u = seg.unit
        head_len, head_wid = theme.head_len * 0.8, theme.head_wid * 0.8
        canvas.line(seg.start, seg.end, width=theme.thin_stroke, color=theme.ink)
        for tip_point, d in ((seg.end, u), (seg.start, -u)):
            back = tip_point - d * head_len
            side = d.perpendicular() * (head_wid / 2.0)
            canvas.polygon((tip_point, back + side, back - side), fill=theme.ink)

        n = seg.normal * math.copysign(1.0, self.offset or 1.0)
        ext = abs(self.offset) + self.witness_ext
        a, b = self._orig
        canvas.line(a, a + n * ext, width=theme.thin_stroke * 0.9, color=theme.ink)
        canvas.line(b, b + n * ext, width=theme.thin_stroke * 0.9, color=theme.ink)

        mid = seg.midpoint + n * (abs(self.offset) * 0.45)
        rot = u.angle_deg
        if rot > 90.0 or rot < -90.0:
            rot += 180.0
        text = self.label_text
        if text is None:
            text = f"{seg.length:.2f}"
        canvas.text(
            mid,
            text,
            size=theme.font_size * 0.92,
            color=theme.ink,
            italic=True,
            halign="middle",
            rotation_deg=rot,
        )
