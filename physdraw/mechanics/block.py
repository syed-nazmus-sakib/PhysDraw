from __future__ import annotations

from typing import TYPE_CHECKING

from ..constraints.geometric import place_on_surface
from ..core.object import SceneObject
from ..core.relations import ON_SURFACE, OnSurface
from ..geometry import Point, Transform, Vector
from ..render.canvas import Canvas

if TYPE_CHECKING:
    from ..core.scene import Scene


class Block(SceneObject):
    """A rectangular rigid body. Attach it to a surface with ``.on(surface)``."""

    kind = "block"
    z = 20
    ANCHORS = (
        "center",
        "top",
        "bottom",
        "left",
        "right",
        "tl",
        "tr",
        "bl",
        "br",
        "contact",
    )

    def __init__(
        self,
        label: str = "",
        *,
        width: float = 1.5,
        height: float = 1.0,
        show_label: bool | None = None,
        **kwargs,
    ) -> None:
        super().__init__(label=label if label else None, **kwargs)
        self.width = width
        self.height = height
        self.show_label = label != "" if show_label is None else show_label
        self._surface = None
        self._t: float = 0.5
        self._transform: Transform = Transform.identity()
        self._corners: tuple[Point, ...] = ()

    # -- relations ----------------------------------------------------------

    def on(self, surface, t: float = 0.5) -> "Block":
        """Declare that this block rests on `surface`, at fraction t along it."""
        assert self.scene is not None
        self.scene.relate(OnSurface(subject=self, target=surface, t=t))
        self._surface = surface
        self._t = t
        return self

    def deps(self) -> list["SceneObject"]:
        return [self._surface] if self._surface is not None else []

    def place(self, scene: "Scene") -> None:
        rels = scene.relations_of(subject=self, kind=ON_SURFACE)
        if rels:
            rel = rels[0]
            transform = place_on_surface(
                self.width, self.height, rel.target.surface_segment(), rel.t
            )
        else:
            transform = Transform.translate(Vector(0.0, self.height / 2.0))
        self._apply_transform(scene, transform)

    def _apply_transform(self, scene: "Scene", transform: Transform) -> None:
        self._transform = transform
        w2, h2 = self.width / 2.0, self.height / 2.0
        local = [
            Point(-w2, -h2),
            Point(w2, -h2),
            Point(w2, h2),
            Point(-w2, h2),
        ]
        self._corners = tuple(self._transform.apply_point(p) for p in local)
        super().place(scene)

    @property
    def transform(self) -> Transform:
        return self._transform

    @property
    def corners(self) -> tuple[Point, ...]:
        return self._corners

    def local_to_world(self, p: Point) -> Point:
        return self._transform.apply_point(p)

    # -- anchors ----------------------------------------------------------

    def anchor_point(self, name: str) -> Point:
        w2, h2 = self.width / 2.0, self.height / 2.0
        match name:
            case "center":
                return self._transform.apply_point(Point(0.0, 0.0))
            case "bottom" | "contact":
                return self._transform.apply_point(Point(0.0, -h2))
            case "top":
                return self._transform.apply_point(Point(0.0, h2))
            case "left":
                return self._transform.apply_point(Point(-w2, 0.0))
            case "right":
                return self._transform.apply_point(Point(w2, 0.0))
            case "bl":
                return self._corners[0]
            case "br":
                return self._corners[1]
            case "tr":
                return self._corners[2]
            case "tl":
                return self._corners[3]
        raise KeyError(name)

    # -- rendering --------------------------------------------------------

    def render(self, canvas: Canvas, theme) -> None:
        canvas.polygon(
            self._corners,
            fill=theme.body_fill,
            stroke=theme.ink,
            width=theme.stroke_width,
        )
        if self.show_label and self.label:
            canvas.text(
                self.anchor_point("center"),
                self.label,
                size=theme.font_size,
                color=theme.ink,
                italic=True,
                halign="middle",
            )


class HangingBlock(Block):
    """A block hanging from the vertical run of a rope over a pulley.

    ``connect(...)`` binds it automatically; its top face is placed `drop`
    units below the pulley's vertical tangent point.
    """

    kind = "block"
    z = Block.z

    def __init__(
        self,
        label: str = "",
        *,
        width: float = 1.05,
        height: float = 0.95,
        drop: float = 1.7,
        **kwargs,
    ) -> None:
        super().__init__(label, width=width, height=height, **kwargs)
        self.drop = drop
        self._hang_pulley = None
        self._hang_sign: int | None = None

    def bind_pulley(self, pulley, side: str) -> "HangingBlock":
        if side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")
        self._hang_pulley = pulley
        self._hang_sign = 1 if side == "right" else -1
        return self

    def deps(self) -> list["SceneObject"]:
        return [self._hang_pulley] if self._hang_pulley is not None else []

    @property
    def hanging_side(self) -> str | None:
        if self._hang_sign is None:
            return None
        return "right" if self._hang_sign == 1 else "left"

    def place(self, scene: "Scene") -> None:
        if self._hang_pulley is None:
            super().place(scene)
            return
        c = self._hang_pulley.anchor("center")
        top_x = c.x + self._hang_sign * self._hang_pulley.radius
        transform = Transform.translate(Vector(top_x, c.y - self.drop - self.height / 2.0))
        self._apply_transform(scene, transform)
