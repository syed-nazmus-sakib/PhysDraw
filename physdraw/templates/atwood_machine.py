from __future__ import annotations

from ..core.scene import Scene
from ..geometry import Point
from ..mechanics.block import HangingBlock
from ..mechanics.forces import Tension, Weight
from ..mechanics.pulley import Pulley
from ..mechanics.rope import connect
from ..style.theme import TEXTBOOK, Theme


def atwood_machine(
    *,
    mass_left: str = "m\u2081",
    mass_right: str = "m\u2082",
    tension: bool = True,
    pulley_at: Point | None = None,
    radius: float = 0.85,
    theme: Theme = TEXTBOOK,
) -> Scene:
    """Two hanging masses over a single pulley."""
    with Scene(theme=theme) as scene:
        kwargs = {"at": pulley_at} if pulley_at is not None else {}
        pulley = Pulley(radius=radius, **kwargs)
        left = HangingBlock(mass_left)
        right = HangingBlock(mass_right)
        connect(left, right, via=pulley)
        Weight(left)
        Weight(right)
        if tension:
            Tension(left)
            Tension(right)
    return scene
