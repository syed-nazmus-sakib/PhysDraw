from __future__ import annotations

from ..core.object import SceneObject
from ..core.relations import CONNECTED_TO, ON_SURFACE, ConnectedTo
from ..geometry import Point, external_tangents
from ..render.canvas import ArcSeg, Canvas
from .block import Block, HangingBlock


def _on_surface(scene, obj) -> bool:
    return bool(scene.relations_of(subject=obj, kind=ON_SURFACE))


class Rope(SceneObject):
    """A taut rope joining two bodies, optionally riding over a pulley."""

    kind = "rope"
    z = 25
    ANCHORS = ("start", "end", "over_start", "over_end")

    def __init__(
        self,
        body_a: SceneObject,
        body_b: SceneObject,
        *,
        via=None,
        attach_a=None,
        attach_b=None,
        name: str | None = None,
        scene=None,
    ) -> None:
        super().__init__(name=name, scene=scene)
        self.a = body_a
        self.b = body_b
        self.via = via
        self.attach_a = attach_a
        self.attach_b = attach_b
        self._pa: Point | None = None
        self._pb: Point | None = None
        self._ta: Point | None = None
        self._tb: Point | None = None
        self._arc_start: float = 0.0
        self._arc_sweep: float = 0.0

    def deps(self) -> list["SceneObject"]:
        out = [self.a, self.b]
        if self.via is not None:
            out.append(self.via)
        return out

    # -- geometry helpers ---------------------------------------------------

    def _roles(self, scene) -> tuple[str, str]:
        role_a = "surface" if _on_surface(scene, self.a) else "hang"
        role_b = "surface" if _on_surface(scene, self.b) else "hang"
        return role_a, role_b

    def _attach_point(self, scene, body, role: str) -> Point:
        spec = self.attach_a if body is self.a else self.attach_b
        if spec is not None:
            from ..core.anchors import resolve_ref

            return resolve_ref(spec)
        if role == "surface":
            rel = scene.relations_of(subject=body, kind=ON_SURFACE)[0]
            face = "left" if getattr(rel.target, "flip", False) else "right"
            return body.anchor(face)
        if isinstance(body, HangingBlock):
            return body.anchor("top")
        return body.anchor("center")

    def _choose_tangent(self, p: Point, c: Point, r: float, exit_deg: float) -> tuple[Point, float]:
        """Pick the external tangent whose wrap reaches `exit_deg` over the top."""
        best = None
        for t in external_tangents(p, c, r):
            a0 = (t - c).angle_deg % 360.0
            if not 90.0 <= a0 <= 270.0:
                continue
            cw = (exit_deg - a0) % 360.0
            sweep = cw if cw <= 180.0 else cw - 360.0
            key = abs(sweep)
            if best is None or key < best[0]:
                best = (key, t, sweep)
        if best is None:
            candidates = []
            for t in external_tangents(p, c, r):
                a0 = (t - c).angle_deg % 360.0
                cw = (exit_deg - a0) % 360.0
                candidates.append((abs(cw if cw <= 180 else cw - 360.0), t))
            _, t = min(candidates)
            a0 = (t - c).angle_deg % 360.0
            cw = (exit_deg - a0) % 360.0
            best = (abs(cw if cw <= 180 else cw - 360.0), t, cw if cw <= 180.0 else cw - 360.0)
        return best[1], best[2]

    # -- layout -------------------------------------------------------------

    def place(self, scene) -> None:
        role_a, role_b = self._roles(scene)

        if self.via is not None:
            surface_roles = [r for r in (role_a, role_b) if r == "surface"]
            if len(surface_roles) == 2:
                raise NotImplementedError(
                    "belt between two supported bodies is not supported yet"
                )
            for role, e in ((role_a, self.a), (role_b, self.b)):
                if role != "surface" and not isinstance(e, HangingBlock):
                    raise ValueError(
                        f"free endpoint '{e.id}' must be a HangingBlock when using a pulley"
                    )

        pa = self._attach_point(scene, self.a, role_a)
        pb = self._attach_point(scene, self.b, role_b)
        self._pa, self._pb = pa, pb

        if self.via is None:
            super().place(scene)
            return

        c = self.via.anchor("center")
        r = self.via.radius

        if role_a == "surface":
            hb = self.b
        else:
            hb = self.a
        side = getattr(hb, "hanging_side", None) or "right"
        exit_deg = 0.0 if side == "right" else 180.0
        sign = 1.0 if side == "right" else -1.0
        t_exit = Point(c.x + sign * r, c.y)

        if role_a == "surface":
            t_in, sweep = self._choose_tangent(pa, c, r, exit_deg)
            self._ta, self._tb = t_in, t_exit
            self._arc_sweep = sweep
            self._arc_start = ((t_in - c).angle_deg % 360.0)
        elif role_b == "surface":
            t_in, sweep = self._choose_tangent(pb, c, r, exit_deg)
            self._ta, self._tb = t_exit, t_in
            self._arc_sweep = sweep
            self._arc_start = ((t_exit - c).angle_deg % 360.0)
        else:
            left = Point(c.x - r, c.y)
            right = Point(c.x + r, c.y)
            self._ta, self._tb = left, right
            self._arc_start = 180.0
            self._arc_sweep = -180.0
        super().place(scene)

    # -- anchors ----------------------------------------------------------

    @property
    def arc_params(self) -> tuple[float, float]:
        return self._arc_start, self._arc_sweep

    def anchor_point(self, name: str) -> Point:
        match name:
            case "start":
                return self._pa
            case "end":
                return self._pb
            case "over_start":
                return self._ta
            case "over_end":
                return self._tb
        raise KeyError(name)

    # -- rendering --------------------------------------------------------

    def render(self, canvas: Canvas, theme) -> None:
        width = getattr(theme, "rope_stroke", 0.06)
        color = theme.ink
        if self.via is None:
            canvas.line(self._pa, self._pb, width=width, color=color)
            return
        canvas.line(self._pa, self._ta, width=width, color=color)
        canvas.add(
            ArcSeg(
                center=self.via.anchor("center"),
                radius=self.via.radius,
                start_deg=self._arc_start,
                sweep_deg=self._arc_sweep,
                width=width,
                color=color,
            )
        )
        canvas.line(self._tb, self._pb, width=width, color=color)


def connect(a: Block, b: Block, *, via=None, name: str | None = None) -> Rope:
    """Declare that blocks `a` and `b` are joined by a rope, optionally over a pulley."""
    scene = a.scene
    if scene is None:
        raise ValueError("both bodies must belong to a scene before connecting")
    rope = Rope(a, b, via=via, name=name, scene=scene)
    scene.relate(ConnectedTo(subject=a, target=b, via=rope, kind=CONNECTED_TO))

    surf_ends = [
        (e, scene.relations_of(subject=e, kind=ON_SURFACE)[0].target)
        for e in (a, b)
        if _on_surface(scene, e)
    ]
    free_ends = [e for e in (a, b) if not any(e is s[0] for s in surf_ends)]

    if via is not None and len(surf_ends) == 1:
        via._bind_mount(surf_ends[0][0], surf_ends[0][1])
        flip = getattr(surf_ends[0][1], "flip", False)
        side = "left" if flip else "right"
        for e in free_ends:
            if isinstance(e, HangingBlock):
                e.bind_pulley(via, side)
    elif via is not None:
        default_sides = ("left", "right")
        for i, e in enumerate(free_ends):
            side = default_sides[i] if i < len(default_sides) else "right"
            if isinstance(e, HangingBlock):
                e.bind_pulley(via, side)
    return rope
