from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Union

from ..geometry import Point
from .object import SceneObject


@dataclass(frozen=True)
class AnchorRef:
    """A symbolic reference to a named anchor on a scene object.

    Resolves to a concrete Point only after layout. Annotations hold AnchorRefs
    so diagrams can be declared before any geometry exists.
    """

    owner: SceneObject
    name: str

    def resolve(self) -> Point:
        return self.owner.anchor(self.name)


RefSpec = Union[Point, AnchorRef, tuple["SceneObject", str], Callable[[], Point], "SceneObject"]


def resolve_ref(ref: RefSpec) -> Point:
    if isinstance(ref, Point):
        return ref
    if isinstance(ref, AnchorRef):
        return ref.resolve()
    if isinstance(ref, SceneObject):
        return ref.anchor("center")
    if isinstance(ref, tuple):
        owner, name = ref
        return owner.anchor(name)
    if callable(ref):
        return ref()
    raise TypeError(f"cannot resolve {ref!r} to a point")


def aref(obj: SceneObject, name: str = "center") -> AnchorRef:
    return AnchorRef(obj, name)
