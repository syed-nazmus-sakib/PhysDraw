from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Optional

from ..constraints.solver import resolve_scene
from ..geometry import Point
from ..render.canvas import Canvas
from ..render.svg import render_svg
from . import state

if TYPE_CHECKING:
    from .object import SceneObject


class Scene:
    """A physics scene graph: objects + semantic relations.

    Usage::

        with Scene() as s:
            plane = Incline(30)
            block = Block("m").on(plane)
            Weight(block); Normal(block); Friction(block)

        s.save("figure.svg")
    """

    def __init__(self, *, theme=None) -> None:
        if theme is None:
            from ..style.theme import TEXTBOOK

            theme = TEXTBOOK
        self.theme = theme
        self.objects: list["SceneObject"] = []
        self.relations: list = []
        self.resolved = False

    # -- construction ---------------------------------------------------------

    def add(self, obj: "SceneObject") -> "SceneObject":
        if obj.scene is not None and obj.scene is not self:
            raise ValueError(f"{obj.id} already belongs to another scene")
        if any(o.id == obj.id for o in self.objects):
            raise ValueError(f"duplicate object id '{obj.id}' in scene")
        self.objects.append(obj)
        obj.scene = self
        return obj

    def relate(self, relation) -> None:
        self.relations.append(relation)

    def relations_of(self, subject=None, kind: str | None = None) -> list:
        return [
            r
            for r in self.relations
            if (subject is None or r.subject is subject)
            and (kind is None or r.kind == kind)
        ]

    def __iter__(self) -> Iterator["SceneObject"]:
        return iter(self.objects)

    def __len__(self) -> int:
        return len(self.objects)

    def __enter__(self) -> "Scene":
        state.push_scene(self)
        return self

    def __exit__(self, *exc) -> None:
        state.pop_scene()

    # -- layout ---------------------------------------------------------------

    def resolve(self) -> "Scene":
        if not self.resolved:
            resolve_scene(self)
            self.resolved = True
        return self

    # -- anchors --------------------------------------------------------------

    def anchor_point(self, obj_id_or_obj, name: str) -> Point:
        obj = obj_id_or_obj
        if isinstance(obj, str):
            for o in self.objects:
                if o.id == obj:
                    obj = o
                    break
            else:
                raise KeyError(f"no object '{obj}' in scene")
        self.resolve()
        return obj.anchor(name)

    # -- rendering ------------------------------------------------------------

    def _canvas(self) -> Canvas:
        self.resolve()
        canvas = Canvas(default_font_family=self.theme.font_family)
        ordered = sorted(
            enumerate(self.objects), key=lambda pair: (pair[1].z, pair[0])
        )
        for _, obj in ordered:
            with canvas.group(obj.id):
                obj.render(canvas, self.theme)
        return canvas

    def to_svg(self) -> str:
        canvas = self._canvas()
        return render_svg(canvas.items, margin=self.theme.margin, paper=self.theme.paper)

    def save(self, path: str) -> str:
        """Render the scene to an SVG file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_svg())
        return path

    def show(self, path: str | None = None) -> str:
        """Write the SVG and try to open it in the default browser."""
        import os
        import tempfile
        import webbrowser

        if path is None:
            fd, path = tempfile.mkstemp(suffix=".svg", prefix="physdraw-")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(self.to_svg())
        elif not os.path.exists(path):
            self.save(path)
        try:
            webbrowser.open(f"file://{os.path.abspath(path)}")
        except Exception:
            pass
        return os.path.abspath(path)


def current_scene(create: bool = False) -> Optional[Scene]:
    return state.active_scene(create=create)


def draw() -> Scene:
    """Resolve and return the implicit default scene."""
    scene = current_scene(create=True)
    assert scene is not None
    return scene.resolve()


def reset() -> None:
    """Discard the implicit default scene so a fresh diagram can be built."""
    state.reset_default()
