from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ..core.anchors import resolve_ref
from ..core.object import SceneObject
from ..core.relations import ON_SURFACE
from ..geometry import Point, Segment, Vector
from ..render.canvas import Canvas

if TYPE_CHECKING:
    from ..core.scene import Scene


DirectionSpec = Union[Vector, float, int, str, tuple[float, float]]


def surface_segment_of(body: SceneObject, scene: "Scene") -> Segment | None:
    rels = scene.relations_of(subject=body, kind=ON_SURFACE)
    return rels[0].target.surface_segment() if rels else None


def resolve_direction(spec: DirectionSpec, body=None, scene=None) -> Vector:
    """Interpret a direction spec as a unit vector in world space."""
    if isinstance(spec, Vector):
        return spec.normalized()
    if isinstance(spec, tuple):
        return Vector(*spec).normalized()
    if isinstance(spec, (int, float)):
        return Vector.from_polar(float(spec))
    s = str(spec)
    if s == "down":
        return Vector(0.0, -1.0)
    if s == "up":
        return Vector(0.0, 1.0)
    if s == "left":
        return Vector(-1.0, 0.0)
    if s == "right":
        return Vector(1.0, 0.0)
    seg = surface_segment_of(body, scene) if (body is not None and scene is not None) else None
    if seg is None:
        raise ValueError(f"direction '{s}' requires its body to rest on a surface")
    if s == "normal":
        return seg.normal
    if s == "up_slope":
        return seg.unit
    if s == "down_slope":
        return -seg.unit
    raise ValueError(
        f"unknown direction '{s}' (use a Vector, degrees, 'down', 'normal', 'up_slope', ...)"
    )


def place_label(
    tip: Point,
    d: Vector,
    *,
    head_len: float,
    head_wid: float,
    label_pad: float,
    side: int = 1,
) -> tuple[Point, str]:
    """Choose a label position and text-anchor just beyond an arrow's tip.

    Horizontal-dominant arrows take the label straight beyond the tip;
    vertical-dominant arrows take it beside the tip so it never runs into
    lines below or above.
    """
    pad = head_len * 0.55 + label_pad
    if abs(d.x) >= abs(d.y):
        pos = tip + d * pad
        halign = "start" if d.x > 0 else "end"
    else:
        sx = 1.0 if side >= 0 else -1.0
        pos = tip + Vector(sx * (head_wid * 0.5 + label_pad), 0.0)
        halign = "start" if sx > 0 else "end"
    return pos, halign


class ForceVector(SceneObject):
    """A force arrow attached to a body.

    The tail sits on an anchor of the body (its center by default); the tip lies
    `length` world units away along the resolved direction.
    """

    kind = "force"
    z = 30
    ANCHORS = ("tail", "tip")

    def __init__(
        self,
        body: SceneObject,
        *,
        direction: DirectionSpec,
        label: str | None = None,
        at: object | None = None,
        scale: float = 1.0,
        length: float | None = None,
        lateral: float = 0.0,
        dash: tuple[float, ...] | None = None,
        color: str | None = None,
        name: str | None = None,
        scene=None,
    ) -> None:
        super().__init__(name=name, scene=scene)
        self.body = body
        self.spec = direction
        self.at_spec = at
        self.scale = scale
        self.length = length
        self.lateral = lateral
        self.dash = dash
        self.color = color
        self.label_text = label
        self._tail: Point | None = None
        self._dir: Vector | None = None
        self._tip: Point | None = None

    def default_label(self) -> str:
        return ""

    # -- layout -------------------------------------------------------------

    def deps(self) -> list[SceneObject]:
        out = [self.body]
        if isinstance(self.spec, str) and self.spec in ("normal", "up_slope", "down_slope"):
            rels = self.scene.relations_of(subject=self.body, kind=ON_SURFACE) if self.scene else []
            out += [r.target for r in rels]
        return out

    def _resolve_tail(self) -> Point:
        a = self.at_spec
        if a is None:
            return self.body.anchor("center")
        if isinstance(a, str):
            return self.body.anchor(a)
        return resolve_ref(a)

    def place(self, scene: "Scene") -> None:
        tail = self._resolve_tail()
        d = resolve_direction(self.spec, self.body, scene)
        if self.lateral:
            tail = tail + d.perpendicular() * self.lateral
        length = self.length
        if length is None:
            length = scene.theme.force_length * self.scale
        self._tail = tail
        self._dir = d
        self._tip = tail + d * length
        super().place(scene)

    # -- anchors --------------------------------------------------------------

    def anchor_point(self, name: str) -> Point:
        match name:
            case "tail":
                return self._tail
            case "tip":
                return self._tip
        raise KeyError(name)

    @property
    def tail_point(self) -> Point:
        return self.anchor_point("tail")

    @property
    def tip_point(self) -> Point:
        return self.anchor_point("tip")

    # -- rendering ----------------------------------------------------------

    def render(self, canvas: Canvas, theme) -> None:
        color = self.color or theme.ink
        canvas.arrow(
            self.tail_point,
            self.tip_point,
            width=theme.force_stroke,
            head_len=theme.head_len,
            head_width=theme.head_wid,
            color=color,
            dash=self.dash,
        )
        label = self.label_text
        if label is None:
            label = self.default_label()
        if label:
            pos, halign = place_label(
                self.tip_point,
                self._dir,
                head_len=theme.head_len,
                head_wid=theme.head_wid,
                label_pad=theme.label_pad,
            )
            canvas.text(
                pos,
                label,
                size=theme.font_size,
                color=color,
                italic=True,
                halign=halign,
            )


class Weight(ForceVector):
    """Gravity on a body: straight down."""

    def __init__(self, body: SceneObject, **kwargs) -> None:
        kwargs.setdefault("direction", "down")
        kwargs.setdefault("scale", 0.85)
        super().__init__(body, **kwargs)

    def default_label(self) -> str:
        base = getattr(self.body, "label", None)
        return f"{base}g" if base else "mg"


class Normal(ForceVector):
    """The contact force: perpendicular to the supporting surface, pointing away from it."""

    def __init__(self, body: SceneObject, **kwargs) -> None:
        kwargs.setdefault("direction", "normal")
        kwargs.setdefault("at", "bottom")
        super().__init__(body, **kwargs)

    def default_label(self) -> str:
        return "N"


class Friction(ForceVector):
    """Contact friction along the surface. Defaults to up-slope (opposing slide-down)."""

    def __init__(self, body: SceneObject, **kwargs) -> None:
        kwargs.setdefault("direction", "up_slope")
        kwargs.setdefault("at", "bottom")
        kwargs.setdefault("lateral", 0.06)
        super().__init__(body, **kwargs)

    def default_label(self) -> str:
        return "f"


class Applied(ForceVector):
    """An externally applied push/pull with an explicit direction."""

    def default_label(self) -> str:
        return "F"


class Tension(ForceVector):
    """Rope tension on a body: along the rope, away from it.

    The direction is inferred from context — up-slope for a body resting on a
    surface, straight up for a hanging block — unless given explicitly.
    """

    def __init__(self, body: SceneObject, *, direction: DirectionSpec | None = None, **kwargs) -> None:
        if direction is None:
            direction = self._infer_direction(body)
        kwargs.setdefault("scale", 0.8)
        super().__init__(body, direction=direction, **kwargs)

    @staticmethod
    def _infer_direction(body: SceneObject) -> str:
        scene = getattr(body, "scene", None)
        if scene is not None and scene.relations_of(subject=body, kind=ON_SURFACE):
            return "up_slope"
        from .block import HangingBlock

        if isinstance(body, HangingBlock):
            return "up"
        raise ValueError(
            f"cannot infer tension direction for '{body.id}'; pass direction= explicitly"
        )

    def default_label(self) -> str:
        return "T"


def forces(
    body: SceneObject,
    *,
    weight: bool = True,
    normal: bool = True,
    friction: bool = False,
    tension: bool = False,
) -> list[ForceVector]:
    """Attach the standard free-body-diagram forces to a body."""
    out: list[ForceVector] = []
    if weight:
        out.append(Weight(body))
    if normal:
        out.append(Normal(body))
    if friction:
        out.append(Friction(body))
    if tension:
        out.append(Tension(body))
    return out


class Acceleration(SceneObject):
    """A dashed kinematics arrow parallel to the slope, drawn beside the block."""

    kind = "acceleration"
    z = 30
    ANCHORS = ("tail", "tip")

    def __init__(
        self,
        body: SceneObject,
        *,
        direction: DirectionSpec = "down_slope",
        label: str | None = None,
        scale: float = 0.62,
        dash: tuple[float, ...] = (0.3, 0.18),
        color: str | None = None,
        name: str | None = None,
        scene=None,
    ) -> None:
        super().__init__(name=name, scene=scene)
        self.body = body
        self.spec = direction
        self.scale = scale
        self.dash = dash
        self.color = color
        self.label_text = label if label is not None else "a"
        self._tail: Point | None = None
        self._dir: Vector | None = None
        self._tip: Point | None = None

    def deps(self) -> list[SceneObject]:
        out = [self.body]
        if isinstance(self.spec, str) and self.spec in ("normal", "up_slope", "down_slope"):
            rels = self.scene.relations_of(subject=self.body, kind=ON_SURFACE) if self.scene else []
            out += [r.target for r in rels]
        return out

    def place(self, scene: "Scene") -> None:
        center = self.body.anchor("center")
        d = resolve_direction(self.spec, self.body, scene)
        side = Vector(d.y, -d.x)
        h = getattr(self.body, "height", 1.0)
        lift = h * 0.9 + 0.25
        length = scene.theme.force_length * self.scale
        # keep the whole arrow strictly down-slope of the body so it never
        # crosses the normal-force shaft
        back = max(1.25, length + 0.35)
        tail = center - d * back + side * lift
        self._tail = tail
        self._dir = d
        self._tip = tail + d * length
        super().place(scene)

    def anchor_point(self, name: str) -> Point:
        match name:
            case "tail":
                return self._tail
            case "tip":
                return self._tip
        raise KeyError(name)

    @property
    def tail_point(self) -> Point:
        return self.anchor_point("tail")

    @property
    def tip_point(self) -> Point:
        return self.anchor_point("tip")

    def render(self, canvas: Canvas, theme) -> None:
        color = self.color or theme.ink
        canvas.arrow(
            self.tail_point,
            self.tip_point,
            width=theme.force_stroke,
            head_len=theme.head_len,
            head_width=theme.head_wid,
            color=color,
            dash=self.dash,
        )
        if self.label_text:
            pos, halign = place_label(
                self.tip_point,
                self._dir,
                head_len=theme.head_len,
                head_wid=theme.head_wid,
                label_pad=theme.label_pad,
            )
            canvas.text(
                pos,
                self.label_text,
                size=theme.font_size,
                color=color,
                italic=True,
                halign=halign,
            )
