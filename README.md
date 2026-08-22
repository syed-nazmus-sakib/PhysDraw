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

## Status: v0.1

The six foundation primitives, proven against the classic inclined-block
diagram:

| Primitive       | Purpose                                            |
|-----------------|----------------------------------------------------|
| `Incline`       | wedge with slope angle θ, ground line, hatching    |
| `Block`         | rectangular rigid body; `.on(surface)`             |
| `ForceVector`   | arrows (`Weight`, `Normal`, `Friction`, `Applied`) |
| `AngleMark`     | arc marking an angle between two directions        |
| `Label`         | free text anchored to an object's anchor           |
| `Dimension`     | dimension line between two anchors                 |

Supported recipe variants:

```python
inclined_block(30)                      # weight + normal
inclined_block(30)                      # friction on by default
inclined_block(30, friction=False)      # frictionless
inclined_block(30, applied="up_slope")  # external force F along the slope
inclined_block(30, applied=25)          # F at 25 degrees
inclined_block(30, acceleration=True)   # dashed kinematics arrow a
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
  (`block.center`, `block.contact`, `incline.toe`, `force.tip`, ...).
  Annotations reference them symbolically before layout exists.
- **Hard vs soft separation.** Geometric relations (block flush on surface,
  N ⟂ surface) are satisfied exactly during layout; visual preferences
  (label offsets, spacing) live in the theme/heuristics layer.
- **Editable SVG.** Output is grouped per object: `<g id="block-m">`,
  `<g id="force-N">`, ready for post-processing or TikZ-style export later.

## Layout model (v0.1)

Placement rules are deterministic and closed-form: the resolver topologically
sorts objects by declared dependencies and each object computes its transform
from its relations (`place_on_surface` rotates a body onto the surface tangent
and offsets it along the surface normal). This satisfies every hard constraint
of current diagram classes exactly — no numerical relaxation needed yet. The
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

- v0.2: pulleys + ropes (`connect(A, B, Pulley())`), springs, rods;
  more anchors; label collision avoidance as soft constraints
- v0.3: TikZ exporter (same primitives IR), PNG export
- later: `.phys` declarative file language compiling to the same IR,
  Manim animation backend, template library (`AtwoodMachine`,
  `SliderCrank`, ...)
