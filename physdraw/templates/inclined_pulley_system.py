from __future__ import annotations

from ..core.scene import Scene
from ..mechanics.block import Block, HangingBlock
from ..mechanics.forces import Friction, Normal, Tension, Weight
from ..mechanics.incline import Incline
from ..mechanics.pulley import Pulley
from ..mechanics.rope import connect
from ..style.theme import TEXTBOOK, Theme


def inclined_pulley_system(
    theta: float = 30.0,
    *,
    mass_on_slope: str = "m\u2081",
    mass_hanging: str = "m\u2082",
    friction: bool = False,
    tension: bool = True,
    show_angle: bool = True,
    incline_length: float = 6.0,
    position_on_slope: float = 0.55,
    theme: Theme = TEXTBOOK,
) -> Scene:
    """Block on an incline connected over a pulley to a hanging block."""
    with Scene(theme=theme) as scene:
        plane = Incline(theta, length=incline_length, show_angle=show_angle)
        on_slope = Block(mass_on_slope).on(plane, position_on_slope)
        hanging = HangingBlock(mass_hanging)

        pulley = Pulley()
        connect(on_slope, hanging, via=pulley)

        Weight(on_slope)
        Normal(on_slope)
        if friction:
            Friction(on_slope)
        if tension:
            Tension(on_slope)
        Weight(hanging)
        if tension:
            Tension(hanging)
    return scene
