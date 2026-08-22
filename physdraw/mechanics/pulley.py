from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.anchors import resolve_ref
from ..core.object import SceneObject
from ..geometry import Point
from ..render.canvas import Canvas

if TYPE_CHECKING:
    from ..core.scene import Scene


class Pulley(SceneObject):
    """A disk the rope rides over.

    Position it explicitly with ``at=`` (or leave it unplaced for an Atwood
    setup), or let ``connect(...)`` auto-mount it just above the apex of the
    incline its first body rests on.
    """

    kind = "pulley"
    z = 16
    ANCHORS = ("center", "axle", "rim_top")

    def __init__(
        self,
        *,
        radius: float = 0.75,
        at=None,
        name: str | None = None,
        scene=None,
    ) -> None:
        super().__init__(name=name, scene=scene)
        self.radius = float(radius)
        self.at_spec = at
        self._mount_ref: tuple[SceneObject, SceneObject] | None = None
        self.auto_mounted = False
        self._center: Point | None = None
        self._strut_from: Point | None = None

    def _bind_mount(self, body: SceneObject, surface: SceneObject) -> None:
        """Record an auto-mount target (called by ``connect``)."""
        if self.at_spec is not None:
            raise ValueError(f"pulley '{self.id}' already has an explicit position")
        self._mount_ref = (body, surface)

    # -- layout ---------------------------------------------------------------

    def deps(self) -> list["SceneObject"]:
        out: list[SceneObject] = []
        if self.at_spec is not None:
            owner = getattr(self.at_spec, "owner", None)
            if isinstance(self.at_spec, tuple) and isinstance(self.at_spec[0], SceneObject):
                out.append(self.at_spec[0])
            elif owner is not None:
                out.append(owner)
        if self._mount_ref is not None:
            out += list(self._mount_ref)
        return out

    def place(self, scene: "Scene") -> None:
        if self.at_spec is not None:
            self._center = resolve_ref(self.at_spec)
        elif self._mount_ref is not None:
            _body, surface = self._mount_ref
            seg = surface.surface_segment()
            apex = (
                surface.anchor("apex")
                if "apex" in getattr(surface, "ANCHORS", ())
                else seg.end
            )
            lift = self.radius / max(abs(seg.unit.x), 0.35) + 0.22
            self._center = Point(apex.x, apex.y + lift)
            self._strut_from = apex
            self.auto_mounted = True
        else:
            self._center = Point(0.0, 4.6)
        super().place(scene)

    # -- anchors ----------------------------------------------------------------

    @property
    def center(self) -> Point:
        return self.anchor_point("center")

    def anchor_point(self, name: str) -> Point:
        match name:
            case "center" | "axle":
                return self._center
            case "rim_top":
                return Point(self._center.x, self._center.y + self.radius)
        raise KeyError(name)

    # -- rendering ----------------------------------------------------------

    def render(self, canvas: Canvas, theme) -> None:
        if self._strut_from is not None:
            canvas.line(
                self._strut_from,
                self.center,
                width=theme.thin_stroke,
                color=theme.ink,
            )
        canvas.circle(
            self.center,
            self.radius,
            fill=theme.paper,
            stroke=theme.ink,
            width=theme.stroke_width,
        )
        canvas.circle(self.center, max(0.09, self.radius * 0.16), fill=theme.ink)
