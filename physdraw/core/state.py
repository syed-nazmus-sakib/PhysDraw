from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .scene import Scene

_lock = threading.Lock()
_stack: list["Scene"] = []
_default: Optional["Scene"] = None


def active_scene(create: bool = False) -> Optional["Scene"]:
    """The scene new objects register into: the innermost explicit scene, else a lazy default."""
    global _default
    with _lock:
        if _stack:
            return _stack[-1]
        if _default is None and create:
            from .scene import Scene

            _default = Scene()
        return _default


def push_scene(scene: "Scene") -> None:
    with _lock:
        _stack.append(scene)


def pop_scene() -> None:
    with _lock:
        if _stack:
            _stack.pop()


def reset_default() -> None:
    """Discard the implicit default scene (used by ``physdraw.reset``)."""
    global _default
    with _lock:
        _default = None
