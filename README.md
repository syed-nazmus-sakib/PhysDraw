# physdraw

A declarative Python DSL for **textbook-grade physics diagrams**.

You describe the *physics* — objects and their relations. The library resolves
the geometry and renders an SVG. Coordinates are an implementation detail.

```python
from physdraw import *

plane = Incline(30)
block = Block("m").on(plane)

Weight(block)
Normal(block)
Friction(block)

draw().save("figure.svg")
```

Or, for common setups, a one-line recipe:

```python
inclined_block(angle=45, mass="m", friction=True).show()
```

Systems compose too:

```python
plane = Incline(30)
a = Block("m₁").on(plane)
b = HangingBlock("m₂")

connect(a, b, Pulley())

Weight(a); Normal(a); Tension(a)
Weight(b); Tension(b)

draw().show()
```

## Status: v0.2

Foundation primitives plus the first connected system:

| Primitive       | Purpose                                                   |
|-----------------|-----------------------------------------------------------|
| `Incline`       | wedge with slope angle θ, ground line, hatching           |
| `Block`         | rectangular rigid body; `.on(surface)`                    |
| `HangingBlock`  | block hanging from a rope run over a pulley               |
| `Pulley`        | disk; auto-mounts above the incline apex when connected   |
| `Rope` / `connect()` | taut connector; exact tangency, wraps over the top   |
| `ForceVector`   | arrows (`Weight`, `Normal`, `Friction`, `Applied`, `Tension`) |
| `AngleMark`     | arc marking an angle between two directions               |
| `Label`         | free text anchored to an object's anchor                  |
| `Dimension`     | dimension line between two anchors                        |

Supported recipes:

```python
inclined_block(30)                      # weight + normal + friction
inclined_block(30, friction=False)      # frictionless
inclined_block(30, applied="up_slope")  # external force F along the slope
inclined_block(30, acceleration=True)   # dashed kinematics arrow a

inclined_pulley_system(30)              # block on slope ↔ hanging mass
inclined_pulley_system(45, friction=True)
atwood_machine()                        # two masses over one pulley
```

Run the gallery:

```bash
python examples/incline_gallery.py   # writes examples/out/*.svg
```

## Architecture

```
┌────────────────────────────────────────────┐
│ 1. USER LANGUAGE                           │
│ Incline(), Block(), Weight(), .on() ...    │
└──────────────────┬─────────────────────────┘
                   ▼
┌────────────────────────────────────────────┐
│ 2. SCENE GRAPH / IR            core/       │
│ objects + semantic relations               │
│ OnSurface(subject, target, t)              │
└──────────────────┬─────────────────────────┘
                   ▼
┌────────────────────────────────────────────┐
│ 3. GEOMETRY KERNEL          geometry/      │
│ Point, Vector, Segment, Arc, Transform     │
│ anchors on every object                    │
└──────────────────┬─────────────────────────┘
                   ▼
┌────────────────────────────────────────────┐
│ 4. LAYOUT RESOLVER       constraints/      │
│ topological order over dependencies;       │
│ hard geometric constraints satisfied       │
│ exactly by construction (v0.1)             │
└──────────────────┬─────────────────────────┘
                   ▼
┌────────────────────────────────────────────┐
│ 5. PRIMITIVES IR             render/       │
│ Seg, Poly, Circle, ArcSeg, Text            │
└──────────────────┬─────────────────────────┘
                   ▼
┌────────────────────────────────────────────┐
│ 6. RENDERER                  render/svg.py │
│ grouped, editable SVG (y-up world space)   │
└────────────────────────────────────────────┘
```

Key properties:

- **Description ≠ drawing.** Objects never touch SVG directly; they emit
  backend-agnostic primitives.
- **Anchors everywhere.** Every object exposes named attachment points
  (`block.center`, `block.contact`, `incline.toe`, `pulley.rim_top`,
  `rope.over_start`, `force.tip`, ...). Annotations reference them
  symbolically before layout exists.
- **Hard vs soft separation.** Geometric relations (blocks flush on surfaces,
  ropes tangent to pulleys, hanging blocks aligned under the vertical run)
  are satisfied exactly during layout; visual preferences (label offsets,
  spacing) live in the theme/heuristics layer.
- **Editable SVG.** Output is grouped per object: `<g id="block-m">`,
  `<g id="rope-1">`, ready for post-processing or TikZ-style export later.

## Layout model

Placement rules are deterministic and closed-form: the resolver topologically
sorts objects by declared dependencies and each object computes its transform
from its relations (`place_on_surface` rotates a body onto the surface tangent;
`connect()` picks the exact external tangent to the pulley and hangs free
blocks under the vertical run). This satisfies every hard constraint of the
current diagram classes exactly — no numerical relaxation needed yet. The
resolver interface (`constraints/solver.py`) is deliberately narrow so a
constraint solver (e.g. Kiwi/Cassowary for soft layout preferences) can slot
in without touching mechanics code.

## Development

```bash
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
.venv/bin/python -m pytest
```

Zero runtime dependencies. Python ≥ 3.10.

## Roadmap

- v0.3: springs, rods, and pin joints (`AttachedTo`); multiple-pulley systems
- v0.4: TikZ exporter (same primitives IR), PNG export
- later: `.phys` declarative file language compiling to the same IR,
  Manim animation backend, template library (`SliderCrank`, ...)
