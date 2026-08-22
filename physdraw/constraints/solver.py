from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.object import SceneObject
    from ..core.scene import Scene


def topological_order(objects: list["SceneObject"]) -> list["SceneObject"]:
    """Stable topological sort by declared dependencies.

    Preserves declaration order among independent objects; raises ValueError
    on cycles or missing dependencies.
    """
    ids = {o.id: o for o in objects}
    remaining: dict[str, set[str]] = {}
    for obj in objects:
        dep_ids: list[str] = []
        for d in obj.deps():
            if d.id not in ids:
                raise ValueError(
                    f"{obj.id} depends on {d.id}, which is not part of the scene"
                )
            if d.id != obj.id:
                dep_ids.append(d.id)
        remaining[obj.id] = set(dep_ids)

    placed: set[str] = set()
    ordered: list["SceneObject"] = []
    pending = list(objects)
    while pending:
        progressed = False
        still_pending = []
        for obj in pending:
            if remaining[obj.id] <= placed:
                ordered.append(obj)
                placed.add(obj.id)
                progressed = True
            else:
                still_pending.append(obj)
        pending = still_pending
        if not progressed and pending:
            stuck = ", ".join(sorted(remaining[o.id] - placed) for o in pending[:3])
            raise ValueError(f"circular dependency in scene involving: {stuck}")
    return ordered


def resolve_scene(scene: "Scene") -> None:
    """Place every object once its dependencies are placed."""
    for obj in topological_order(scene.objects):
        obj.place(scene)
