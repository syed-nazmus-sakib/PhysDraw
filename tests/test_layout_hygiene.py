"""Layout hygiene: labels must not sit on top of lines from other objects."""

from __future__ import annotations

from physdraw import atwood_machine, inclined_block, inclined_pulley_system
from physdraw.render.canvas import Seg, Text


def _text_box(t: Text) -> tuple[float, float, float, float]:
    w = len(t.text) * t.size * 0.62
    h = t.size * 1.1
    x0, x1 = {
        "start": (t.pos.x - h * 0.2, t.pos.x + w),
        "end": (t.pos.x - w, t.pos.x + h * 0.2),
        "middle": (t.pos.x - w / 2.0, t.pos.x + w / 2.0),
    }[t.halign]
    return (x0, t.pos.y - h / 2.0, x1, t.pos.y + h / 2.0)


def _expanded(box, pad):
    return (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)


def _hits(box, seg: Seg, samples: int = 64) -> bool:
    x0, y0, x1, y1 = box
    for i in range(samples + 1):
        s = i / samples
        x = seg.p1.x + (seg.p2.x - seg.p1.x) * s
        y = seg.p1.y + (seg.p2.y - seg.p1.y) * s
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


def _assert_clean(scene) -> None:
    canvas = scene._canvas()
    texts = [(gid, p) for gid, p in canvas.items if isinstance(p, Text)]
    segs = [(gid, p) for gid, p in canvas.items if isinstance(p, Seg)]
    offenders = []
    for tgid, text in texts:
        if not text.text.strip():
            continue
        box = _expanded(_text_box(text), 0.04)
        for sgid, seg in segs:
            if sgid == tgid:
                continue
            if _hits(box, seg):
                offenders.append((text.text, tgid, sgid))
    assert not offenders, f"label/line collisions: {offenders}"


def test_inclined_block_labels_are_clear():
    for angle in (30, 45, 60):
        _assert_clean(inclined_block(angle))
        _assert_clean(inclined_block(angle, friction=False))


def test_inclined_pulley_labels_are_clear():
    for angle in (30, 45, 60):
        _assert_clean(inclined_pulley_system(angle))
        _assert_clean(inclined_pulley_system(angle, friction=True))


def test_atwood_labels_are_clear():
    _assert_clean(atwood_machine())
