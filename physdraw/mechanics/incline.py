from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..core.object import SceneObject
from ..geometry import ORIGIN, Point, Segment, Vector
from ..render.canvas import Canvas

if TYPE_CHECKING:
    from ..core.scene import Scene


class Incline(SceneObject):
    """A wedge: horizontal ground, a slope of length `length`, angle `angle_deg`.

    The toe (where slope meets ground) sits at `toe`. By default the slope
    rises to the right; ``flip=True`` mirrors it.
    """

    kind = "incline"
    z = 10
    ANCHORS = (
        "toe",
        "apex",
        "corner",
        "surface_start",
        "surface_end",
        "surface_mid",
        "base_mid",
    )

    def __init__(
        self,
        angle_deg: float,
        *,
        length: float = 6.0,
        toe: Point | None = None,
        flip: bool = False,
        show_angle: bool = True,
        angle_label: str | None = None,
        ground_extension: float | None = None,
        hatched: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if not 0 < angle_deg < 90:
            raise ValueError("inclination must be strictly between 0 and 90 degrees")
        self.angle_deg = angle_deg
        self.length = length
        self.toe_pos = toe if toe is not None else ORIGIN
        self.flip = flip
        self.show_angle = show_angle
        self.angle_label = angle_label if angle_label is not None else "\u03b8"
        self.ground_extension = ground_extension
        self.hatched = hatched
        self._toe: Point | None = None
        self._apex: Point | None = None
        self._corner: Point | None = None

    # -- geometry ---------------------------------------------------------

    def deps(self) -> list["SceneObject"]:
        return []

    def place(self, scene: "Scene") -> None:
        r = math.radians(self.angle_deg)
        sx = -1.0 if self.flip else 1.0
        self._toe = self.toe_pos
        self._apex = self._toe + Vector(sx * self.length * math.cos(r), self.length * math.sin(r))
        self._corner = Point(self._apex.x, self._toe.y)
        super().place(scene)

    def _require_placed(self) -> None:
        if not self.placed or self._toe is None:
            raise RuntimeError("incline is not placed yet")

    @property
    def toe(self) -> Point:
        self._require_placed()
        return self._toe

    @property
    def apex(self) -> Point:
        self._require_placed()
        return self._apex

    @property
    def corner(self) -> Point:
        self._require_placed()
        return self._corner

    def surface_segment(self) -> Segment:
        return Segment(self.toe, self.apex)

    def base_segment(self) -> Segment:
        return Segment(self.toe, self.corner)

    def surface_point(self, t: float) -> Point:
        return self.surface_segment().point_at(t)

    def upslope(self) -> Vector:
        """Unit vector along the slope pointing uphill."""
        return self.surface_segment().unit

    def downslope(self) -> Vector:
        return -self.upslope()

    def normal(self) -> Vector:
        """Outward unit normal to the slope."""
        return self.surface_segment().normal

    # -- anchors ----------------------------------------------------------

    def anchor_point(self, name: str) -> Point:
        seg = self.surface_segment()
        match name:
            case "toe" | "surface_start":
                return seg.start
            case "apex" | "surface_end":
                return seg.end
            case "corner":
                return self.corner
            case "surface_mid":
                return seg.midpoint
            case "base_mid":
                return self.base_segment().midpoint
        raise KeyError(name)

    # -- rendering --------------------------------------------------------

    def render(self, canvas: Canvas, theme) -> None:
        toe, apex, corner = self.toe, self.apex, self.corner

        canvas.polygon(
            [toe, apex, corner],
            fill=theme.surface_fill,
            stroke=theme.ink,
            width=theme.stroke_width,
        )

        ext = self.ground_extension
        if ext is None:
            ext = max(0.9, self.length * 0.16)
        gx0, gx1 = min(toe.x, corner.x) - ext, max(toe.x, corner.x) + ext
        gy = toe.y
        canvas.line(
            Point(gx0, gy),
            Point(gx1, gy),
            width=theme.thin_stroke,
            color=theme.ink,
        )
        if self.hatched:
            x = gx0 + theme.hatch_gap / 2.0
            hl = theme.hatch_len
            while x < gx1:
                canvas.line(
                    Point(x, gy),
                    Point(x - hl * 0.7071, gy - hl),
                    width=theme.thin_stroke,
                    color=theme.ink,
                )
                x += theme.hatch_gap

        if self.show_angle:
            gdir = (corner - toe).normalized()
            sdir = (apex - toe).normalized()
            radius = min(1.15, self.length * 0.22)
            canvas.arc(
                center=toe,
                radius=radius,
                start_deg=gdir.angle_deg,
                end_deg=sdir.angle_deg,
                width=theme.thin_stroke,
                color=theme.ink,
            )
            mid_deg = (gdir.angle_deg + sdir.angle_deg) / 2.0
            label_pos = toe + Vector.from_polar(mid_deg, radius + theme.label_pad * 1.6)
            canvas.text(
                label_pos,
                self.angle_label,
                size=theme.font_size,
                color=theme.ink,
                italic=True,
                halign="middle",
            )
