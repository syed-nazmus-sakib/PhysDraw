from __future__ import annotations

import xml.etree.ElementTree as ET
from types import SimpleNamespace

from physdraw import (
    Block,
    HangingBlock,
    Incline,
    Normal,
    Pulley,
    Scene,
    Tension,
    Vector,
    Weight,
    atwood_machine,
    connect,
    inclined_pulley_system,
)


def _arc_contains(arc_start: float, sweep: float, target: float = 90.0) -> bool:
    if sweep >= 0:
        return ((target - arc_start) % 360.0) <= sweep + 1e-9
    return ((arc_start - target) % 360.0) <= -sweep + 1e-9


def _incline_pulley_scene() -> SimpleNamespace:
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
    return SimpleNamespace(
        scene=s.resolve(), plane=plane, slope_block=a, hang_block=b, pulley=pulley, rope=rope
    )


def test_rope_is_tangent_to_pulley():
    fx = _incline_pulley_scene()
    c = fx.pulley.anchor("center")
    t_in = fx.rope.anchor("over_start")
    p = fx.rope.anchor("start")
    assert abs((t_in - c).length - fx.pulley.radius) < 1e-9
    assert abs((t_in - c).dot(t_in - p)) < 1e-9


def test_wrap_arc_passes_over_top():
    fx = _incline_pulley_scene()
    start, sweep = fx.rope.arc_params
    assert _arc_contains(start, sweep)


def test_hanging_block_hangs_from_vertical_run():
    fx = _incline_pulley_scene()
    top = fx.hang_block.anchor("top")
    exit_pt = fx.rope.anchor("over_end")
    c = fx.pulley.anchor("center")
    assert abs(top.x - exit_pt.x) < 1e-9
    assert top.y < exit_pt.y
    assert abs(exit_pt.y - c.y) < 1e-9
    assert fx.hang_block.hanging_side == "right"
    assert abs(top.x - (c.x + fx.pulley.radius)) < 1e-9


def test_tension_directions():
    fx = _incline_pulley_scene()
    seg = fx.plane.surface_segment()
    t_slope = next(o for o in fx.scene if isinstance(o, Tension) and o.body is fx.slope_block)
    d = (t_slope.tip_point - t_slope.tail_point).normalized()
    assert d.approx(seg.unit, tol=1e-9)

    t_hang = next(o for o in fx.scene if isinstance(o, Tension) and o.body is fx.hang_block)
    dh = (t_hang.tip_point - t_hang.tail_point).normalized()
    assert dh.approx(Vector(0.0, 1.0))


def test_normal_still_perpendicular_with_system():
    fx = _incline_pulley_scene()
    n = next(o for o in fx.scene if isinstance(o, Normal))
    seg = fx.plane.surface_segment()
    assert abs((n.tip_point - n.tail_point).dot(seg.unit)) < 1e-9


def test_incline_pulley_renders_grouped():
    svg = inclined_pulley_system(45).to_svg()
    root = ET.fromstring(svg)
    ids = [g.get("id") for g in root.iter() if g.tag.endswith("g")]
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
    ET.fromstring(atwood_machine().to_svg())


def test_straight_rope_without_pulley():
    with Scene() as s:
        a = Block("a").on(Incline(30))
        b = Block("b")
        connect(a, b)
    svg = s.to_svg()
    ET.fromstring(svg)
