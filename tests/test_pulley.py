from __future__ import annotations

import xml.etree.ElementTree as ET

from physdraw import (
    Block,
    HangingBlock,
    Incline,
    Normal,
    Pulley,
    Rope,
    Scene,
    Tension,
    Weight,
    atwood_machine,
    connect,
    inclined_pulley_system,
)
from physdraw.geometry import Vector


def _arc_contains(arc_start: float, sweep: float, target: float = 90.0) -> bool:
    if sweep >= 0:
        return ((target - arc_start) % 360.0) <= sweep + 1e-9
    return ((arc_start - target) % 360.0) <= -sweep + 1e-9


def _incline_pulley_scene():
    with Scene() as s:
        plane = Incline(30)
        a = Block("m1").on(plane)
        b = HangingBlock("m2")
        pulley = Pulley()
        rope = connect(a, b, via=pulley)
        Weight(a)
        Normal(a)
        Tension(a)
        Weight(b)
        Tension(b)
    return s.resolve(), plane, a, b, pulley, rope


def test_rope_is_tangent_to_pulley():
    s, plane, a, b, pulley, rope = _incline_pulley_scene()
    c = pulley.anchor("center")
    t_in = rope.anchor("over_start")
    p = rope.anchor("start")
    assert abs((t_in - c).length - pulley.radius) < 1e-9
    assert abs((t_in - c).dot(t_in - p)) < 1e-9


def test_wrap_arc_passes_over_top():
    s, plane, a, b, pulley, rope = _incline_pulley_scene()
    start, sweep = rope.arc_params
    assert _arc_contains(start, sweep)


def test_hanging_block_hangs_from_vertical_run():
    s, plane, a, b, pulley, rope = _incline_pulley_scene()
    top = b.anchor("top")
    exit_pt = rope.anchor("over_end")
    c = pulley.anchor("center")
    assert abs(top.x - exit_pt.x) < 1e-9
    assert top.y < exit_pt.y
    assert abs(exit_pt.y - c.y) < 1e-9
    side = "right"
    expected_x = c.x + (1 if side == "right" else -1) * pulley.radius
    assert b.hanging_side == side
    assert abs(top.x - expected_x) < 1e-9


def test_tension_directions():
    s, plane, a, b, pulley, rope = _incline_pulley_scene()
    seg = plane.surface_segment()
    t_slope = next(o for o in s if isinstance(o, Tension) and o.body is a)
    d = (t_slope.tip_point - t_slope.tail_point).normalized()
    assert d.approx(seg.unit, tol=1e-9)

    t_hang = next(o for o in s if isinstance(o, Tension) and o.body is b)
    dh = (t_hang.tip_point - t_hang.tail_point).normalized()
    assert dh.approx(Vector(0.0, 1.0))


def test_normal_still_perpendicular_with_system():
    s, plane, a, b, pulley, rope = _incline_pulley_scene()
    n = next(o for o in s if isinstance(o, Normal))
    seg = plane.surface_segment()
    assert abs((n.tip_point - n.tail_point).dot(seg.unit)) < 1e-9


def test_incline_pulley_renders_grouped():
    svg = inclined_pulley_system(45).to_svg()
    ET.fromstring(svg)
    ids = [g.get("id") for g in ET.fromstring(svg).iter() if g.tag.endswith("g")]
    kinds = {i.split("-")[0] for i in ids if i}
    assert {"incline", "block", "pulley", "rope", "force"} <= kinds


def test_atwood_machine_symmetry():
    scene = atwood_machine().resolve()
    pulley = next(o for o in scene if isinstance(o, Pulley))
    blocks = [o for o in scene if isinstance(o, HangingBlock)]
    tops = sorted((b.anchor("top").x, b.anchor("top").y) for b in blocks)
    (x_left, y_left), (x_right, y_right) = tops
    assert abs(y_left - y_right) < 1e-9
    center = pulley.anchor("center").x
    r = pulley.radius
    assert abs(x_left - (center - r)) < 1e-9
    assert abs(x_right - (center + r)) < 1e-9
    sides = sorted(b.hanging_side for b in blocks)
    assert sides == ["left", "right"]


def test_atwood_renders():
    svg = atwood_machine().to_svg()
    ET.fromstring(svg)
