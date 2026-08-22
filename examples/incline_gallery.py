"""Generates the v0.1 gallery: every variant the inclined-block recipe must support."""

from __future__ import annotations

import os

from physdraw import (
    Block,
    Dimension,
    Friction,
    Incline,
    Label,
    Normal,
    Scene,
    Vector,
    Weight,
    inclined_block,
)

OUT = os.path.join(os.path.dirname(__file__), "out")


def gallery() -> list[tuple[str, object]]:
    figures = [
        ("inclined_block_30", inclined_block(30)),
        ("inclined_block_45", inclined_block(45)),
        ("inclined_block_60", inclined_block(60)),
        ("no_friction", inclined_block(30, friction=False)),
        ("applied_up_slope", inclined_block(30, applied="up_slope")),
        ("with_acceleration", inclined_block(30, applied="up_slope", acceleration=True)),
    ]

    compositional = Scene()
    with compositional:
        plane = Incline(45)
        body = Block("m").on(plane)
        Weight(body)
        Normal(body)
        Friction(body)
    figures.append(("compositional_45", compositional))

    annotated = inclined_block(30, show_angle=True)
    plane = next(o for o in annotated if o.kind == "incline")
    body = next(o for o in annotated if o.kind == "block")
    with annotated:
        Dimension((plane, "toe"), (plane, "corner"), offset=-0.8, label="L")
        Label("contact", at=(body, "contact"), offset=Vector(-0.5, -0.55), halign="end")
    figures.append(("annotated_30", annotated))

    return figures


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, figure in gallery():
        path = os.path.join(OUT, f"{name}.svg")
        figure.save(path)
        print(f"wrote {path}")
