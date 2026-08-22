# Contributing to physdraw

Thanks for helping build a cleaner way to draw physics.

## Development setup

```bash
git clone <your-fork-url> && cd physdraw
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
source .venv/bin/activate
```

## Before you open a PR

```bash
python -m pytest          # all tests must pass
ruff check .              # no lint errors
```

Generate and inspect the gallery when touching rendering:

```bash
python examples/incline_gallery.py   # writes examples/out/*.svg
```

## How the codebase is organized

```
geometry/     pure math: Point, Vector, Segment, Arc, Transform
core/         scene graph IR: objects, relations, anchors, Scene
constraints/  layout: topological resolver + placement rules
mechanics/    physics nouns: Incline, Block, Pulley, Rope, forces...
render/       backend-agnostic primitives + SVG backend
style/        themes
templates/    one-line recipes built from primitives
```

Guiding rules:

1. **Description ≠ drawing.** New primitives must never emit SVG directly;
   they declare geometry in `place()` and emit primitives in `render()`.
2. **Relations over coordinates.** If a new feature needs absolute positions
   from users, the API design is wrong.
3. **Templates compose primitives.** Never hard-code a second copy of a figure.
4. **Every primitive exposes anchors** (`ANCHORS` tuple) so annotations can
   attach symbolically before layout exists.

## Adding a mechanics primitive

1. Subclass `SceneObject` (see `mechanics/block.py` for the pattern).
2. Set `kind`, `z` (paint order), `ANCHORS`.
3. Implement `deps()`, `place(scene)` (compute concrete geometry), and
   `render(canvas, theme)`.
4. Add tests asserting geometric invariants (perpendicularity, tangency,
   contact) — not just "SVG renders".
5. Add a gallery entry so changes are visible at a glance.

## Commit style

Short imperative subject lines, **four words maximum**, e.g.
`add pulley primitive`, `fix rope tangency math`. Commit early, commit often.

## Reporting bugs

Open an issue with the bug report template; include the snippet, expected
figure, and the SVG output if rendering is involved.
