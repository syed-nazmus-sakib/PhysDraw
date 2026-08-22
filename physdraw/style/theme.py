from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Visual styling for a diagram. All lengths are in world units."""

    name: str = "textbook"
    ink: str = "#16181d"
    paper: str | None = "#ffffff"
    surface_fill: str = "#eef1f4"
    body_fill: str = "#ffffff"

    stroke_width: float = 0.075
    thin_stroke: float = 0.045
    force_stroke: float = 0.095

    font_family: str = "Georgia, 'Times New Roman', serif"
    font_size: float = 0.55

    force_length: float = 2.0
    head_len: float = 0.34
    head_wid: float = 0.21

    hatch_gap: float = 0.42
    hatch_len: float = 0.26

    label_pad: float = 0.24
    margin: float = 0.85


TEXTBOOK = Theme(name="textbook")
