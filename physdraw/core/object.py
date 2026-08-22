from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from ..geometry import Point

if TYPE_CHECKING:
    from .scene import Scene

from . import state


def _slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-")
    return s or "obj"


class SceneObject:
    """Base class for everything that lives in a scene graph.

    Lifecycle: declare (constructor + relations) -> place (layout assigns concrete
    geometry) -> render (emit primitives through a Canvas).
    """

    kind: ClassVar[str] = "object"
    z: ClassVar[int] = 10
    ANCHORS: ClassVar[tuple[str, ...]] = ()

    _counters: ClassVar[dict[str, int]] = {}

    def __init__(
        self,
        *,
        label: str | None = None,
        name: str | None = None,
        scene: "Scene | None" = None,
    ) -> None:
        n = SceneObject._counters.get(self.kind, 0) + 1
        SceneObject._counters[self.kind] = n
        self.id: str = _slug(name) if name else f"{self.kind}-{n}"
        self.label = label
        self.placed = False
        self.scene: "Scene | None" = None
        target = scene if scene is not None else state.active_scene(create=True)
        if target is not None:
            target.add(self)

    # -- layout ---------------------------------------------------------------

    def deps(self) -> list["SceneObject"]:
        """Objects whose geometry must be resolved before this one is placed."""
        return []

    def place(self, scene: "Scene") -> None:
        """Assign concrete geometry from declared properties and relations."""
        self.placed = True

    # -- anchors --------------------------------------------------------------

    def anchor_point(self, name: str) -> Point:
        raise NotImplementedError(
            f"{type(self).__name__} does not implement anchor '{name}'"
        )

    def anchor(self, name: str) -> Point:
        if not self.placed:
            raise RuntimeError(
                f"anchor '{name}' requested before layout: call scene.resolve() first"
            )
        if name not in self.ANCHORS:
            raise KeyError(f"{type(self).__name__} has no anchor '{name}' (has {self.ANCHORS})")
        return self.anchor_point(name)

    # -- rendering ------------------------------------------------------------

    def render(self, canvas, theme) -> None:
        raise NotImplementedError
