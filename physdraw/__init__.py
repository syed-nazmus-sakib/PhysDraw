"""physdraw: a declarative Python DSL for textbook-grade physics diagrams.

Describe the physics — objects and their relations — and the library resolves
the geometry and renders an SVG. Coordinates are an implementation detail.
"""

from .core.relations import OnSurface
from .core.scene import Scene, current_scene, draw, reset
from .geometry import Point, Segment, Transform, Vector
from .mechanics.annotations import AngleMark, Dimension, Label
from .mechanics.block import Block, HangingBlock
from .mechanics.forces import (
    Acceleration,
    Applied,
    ForceVector,
    Friction,
    Normal,
    Tension,
    Weight,
    forces,
)
from .mechanics.incline import Incline
from .mechanics.pulley import Pulley
from .mechanics.rope import Rope, connect
from .style.theme import TEXTBOOK, Theme
from .templates.inclined_block import inclined_block

AppliedForce = Applied

__version__ = "0.1.0"

__all__ = [
    "TEXTBOOK",
    "Acceleration",
    "AngleMark",
    "Applied",
    "AppliedForce",
    "Block",
    "Dimension",
    "ForceVector",
    "Friction",
    "HangingBlock",
    "Incline",
    "Label",
    "Normal",
    "OnSurface",
    "Point",
    "Pulley",
    "Rope",
    "Scene",
    "Segment",
    "Tension",
    "Theme",
    "Transform",
    "Vector",
    "Weight",
    "connect",
    "current_scene",
    "draw",
    "forces",
    "inclined_block",
    "reset",
]


def save(path: str) -> str:
    """Render the implicit default scene to `path` (extension decides format; svg only for now)."""
    return draw().save(path)


def show(path: str | None = None) -> str:
    """Render the implicit default scene and try to open it in a browser."""
    return draw().show(path)
