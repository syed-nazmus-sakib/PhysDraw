from __future__ import annotations

from typing import Union

from ..core.scene import Scene
from ..geometry import Vector
from ..mechanics.block import Block
from ..mechanics.forces import Acceleration, Applied, Friction, Normal, Weight
from ..mechanics.incline import Incline
from ..style.theme import TEXTBOOK, Theme

AppliedSpec = Union[None, str, float, int, Vector]


def inclined_block(
    angle: float = 30.0,
    *,
    mass: str = "m",
    friction: bool = True,
    applied: AppliedSpec = None,
    acceleration: bool = False,
    show_angle: bool = True,
    incline_length: float = 6.0,
    block_width: float = 1.5,
    block_height: float = 1.0,
    position_on_slope: float = 0.55,
    theme: Theme = TEXTBOOK,
) -> Scene:
    """The classic textbook figure: a block resting on an inclined plane.

    Built compositionally from the same primitives a hand-written diagram uses,
    so every part of the result remains editable.
    """
    with Scene(theme=theme) as scene:
        plane = Incline(
            angle,
            length=incline_length,
            show_angle=show_angle,
            angle_label=None if show_angle else "\u03b8",
        )
        body = Block(mass, width=block_width, height=block_height).on(plane, position_on_slope)

        Weight(body)
        Normal(body)
        if friction:
            Friction(body)
        if applied is not None:
            spec: str | float | Vector = applied
            Applied(body, direction=spec)
        if acceleration:
            Acceleration(body)
    return scene
