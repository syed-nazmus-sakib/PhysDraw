from __future__ import annotations

from ..geometry import Segment, Transform


def place_on_surface(width: float, height: float, surface: Segment, t: float) -> Transform:
    """Transform placing a body of `width` x `height` flush on a surface segment.

    The body's local frame is centered at its centroid; the transform rotates it
    so its local +x axis runs along the surface and translates it so the
    midpoint of its bottom face touches the surface at parameter t.
    """
    u = surface.unit
    n = u.perpendicular()
    center = surface.point_at(t) + n * (height / 2.0)
    return Transform(translation=center.to_vector(), rotation_deg=u.angle_deg)
