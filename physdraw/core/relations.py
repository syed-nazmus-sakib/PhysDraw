from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .object import SceneObject

ON_SURFACE = "on_surface"
ATTACHED_TO = "attached_to"
CONNECTED_TO = "connected_to"


@dataclass(frozen=True)
class Relation:
    """A semantic relationship between two scene objects.

    Relations are the IR-level description of a diagram; the layout engine
    turns them into concrete geometry.
    """

    subject: "SceneObject"
    target: "SceneObject"
    kind: str = "relation"

    @property
    def dependent(self) -> "SceneObject":
        return self.subject


@dataclass(frozen=True)
class OnSurface(Relation):
    """`subject` rests on `target`, with its contact face at fraction `t` along it."""

    t: float = 0.5
    kind: str = ON_SURFACE


@dataclass(frozen=True)
class AttachedTo(Relation):
    """`subject` is pinned to an anchor of `target` (future joints, ropes, pivots)."""

    anchor: str | None = None
    kind: str = ATTACHED_TO


@dataclass(frozen=True)
class ConnectedTo(Relation):
    """`subject` is linked to `target` via a connector (ropes, springs, rods)."""

    via: object | None = None
    kind: str = CONNECTED_TO
