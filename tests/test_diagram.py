from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from physdraw import (
    Acceleration,
    Applied,
    Block,
    Dimension,
    Friction,
    Incline,
    Normal,
    Scene,
    Vector,
    Weight,
    inclined_block,
)
from physdraw.mechanics.annotations import Label


def _build_flagship() -> Scene:
    with Scene() as s:
        plane = Incline(30)
        body = Block("m").on(plane)
        Weight(body)
        Normal(body)
        Friction(body)
    return s


def test_flagship_svg_is_valid_and_grouped():
    svg = _build_flagship().to_svg()
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    ids = [g.get("id") for g in root.iter() if g.tag.endswith("g")]
    assert any(i and i.startswith("incline-") for i in ids)
    assert any(i and i.startswith("block-") for i in ids)
    force_groups = [i for i in ids if i and i.startswith("force-")]
    assert len(force_groups) == 3


def test_geometry_invariants():
    s = _build_flagship()
    s.resolve()
    inc = next(o for o in s if o.kind == "incline")
    blk = next(o for o in s if o.kind == "block")

    seg = inc.surface_segment()

    contact = blk.anchor("contact")
    assert seg.distance_to_point(contact) < 1e-9, "block must touch the surface"

    weight = next(o for o in s if isinstance(o, Weight))
    assert weight.tail_point.approx(blk.anchor("center"))
    assert (weight.tip_point - weight.tail_point).approx(Vector(0, -1.7))

    normal = next(o for o in s if isinstance(o, Normal))
    ndir = normal.tip_point - normal.tail_point
    assert abs(ndir.dot(seg.unit)) < 1e-9, "normal must be perpendicular to the surface"
    assert ndir.dot(seg.normal) > 0, "normal must point away from the surface"

    friction = next(o for o in s if isinstance(o, Friction))
    fdir = friction.tip_point - friction.tail_point
    assert abs(fdir.dot(seg.normal)) < 1e-9, "friction must be parallel to the surface"
    assert fdir.dot(seg.unit) > 0, "default friction points up-slope"


def test_anchor_guard_before_resolve():
    with Scene():
        plane = Incline(30)
        blk = Block("m").on(plane)
        with pytest.raises(RuntimeError):
            blk.anchor("center")


@pytest.mark.parametrize("angle", [30, 45, 60])
def test_angle_variants_render(angle):
    svg = inclined_block(angle).to_svg()
    ET.fromstring(svg)


def test_friction_optional():
    with_friction = inclined_block(30, friction=True).to_svg()
    without = inclined_block(30, friction=False).to_svg()
    ET.fromstring(with_friction)
    ET.fromstring(without)
    assert with_friction.count("<g") == without.count("<g") + 1


def test_applied_and_acceleration_variants():
    svg = inclined_block(30, applied="up_slope").to_svg()
    root = ET.fromstring(svg)
    texts = [t.text for t in root.iter() if t.tag.endswith("text")]
    assert "F" in texts

    dashed = inclined_block(30, applied="up_slope", acceleration=True).to_svg()
    root = ET.fromstring(dashed)
    texts = [t.text for t in root.iter() if t.tag.endswith("text")]
    assert "a" in texts
    assert 'stroke-dasharray="' in dashed


def test_label_and_dimension_primitives():
    with Scene() as s:
        plane = Incline(30)
        blk = Block("m").on(plane)
        Label("pivot", at=(blk, "top"), offset=Vector(0.0, 0.4))
        Dimension((plane, "toe"), (plane, "corner"), offset=-0.7, label="L")
    svg = s.to_svg()
    root = ET.fromstring(svg)
    texts = [t.text for t in root.iter() if t.tag.endswith("text")]
    assert "pivot" in texts
    assert "L" in texts


def test_acceleration_class_present():
    assert issubclass(Acceleration, object)


def test_acceleration_arrow_does_not_cross_force_arrows():
    from physdraw.geometry import Segment, segments_intersect

    for angle in (30, 45, 60):
        s = inclined_block(angle, applied="up_slope", acceleration=True).resolve()
        acc = next(o for o in s if isinstance(o, Acceleration))
        aseg = Segment(acc.tail_point, acc.tip_point)
        for cls in (Weight, Normal, Friction, Applied):
            f = next(o for o in s if isinstance(o, cls))
            assert segments_intersect(aseg, Segment(f.tail_point, f.tip_point)) is None


def test_scene_reuse_is_idempotent():
    s = _build_flagship()
    first = s.to_svg()
    second = s.to_svg()
    assert first == second
