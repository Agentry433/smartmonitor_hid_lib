from __future__ import annotations

import importlib
from importlib import import_module
from pathlib import Path
import sys

from .errors import SmartMonitorBridgeError

ENV_PROJECT_ROOT = "SMARTMONITOR_HID_PROJECT_ROOT"

_configured_project_root: Path | None = None


def configure_project_root(path: str | Path | None) -> Path | None:
    global _configured_project_root
    if path in (None, ""):
        _configured_project_root = None
        return None
    resolved = Path(path).expanduser().resolve()
    _configured_project_root = resolved
    return resolved


def get_project_root() -> Path | None:
    if _configured_project_root is not None:
        return _configured_project_root
    value = Path.cwd()
    candidates = [
        Path.cwd(),
        *Path.cwd().parents,
    ]
    env_value = sys.modules.get("os").environ.get(ENV_PROJECT_ROOT) if "os" in sys.modules else None
    if env_value:
        return Path(env_value).expanduser().resolve()
    for candidate in candidates:
        if (candidate / "library").is_dir():
            return candidate
    return value if (value / "library").is_dir() else None


def _iter_candidate_roots() -> list[Path]:
    candidates: list[Path] = []
    if _configured_project_root is not None:
        candidates.append(_configured_project_root)
    env_value = __import__("os").environ.get(ENV_PROJECT_ROOT)
    if env_value:
        candidates.append(Path(env_value).expanduser().resolve())
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        unique.append(candidate)
    return unique


def _is_project_root(path: Path) -> bool:
    return (path / "library").is_dir()


def _module_belongs_to_root(module, root: Path) -> bool:
    module_file = getattr(module, "__file__", None)
    if not module_file:
        return False
    try:
        Path(module_file).resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def import_project_module(module_name: str):
    errors: list[Exception] = []
    for candidate_root in _iter_candidate_roots():
        if not _is_project_root(candidate_root):
            continue
        inserted = False
        candidate_str = str(candidate_root)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)
            inserted = True
        package_name = module_name.split(".", 1)[0]
        previous_package = sys.modules.get(package_name)
        previous_module = sys.modules.get(module_name)
        removed_package = False
        removed_module = False
        if previous_package is not None and not _module_belongs_to_root(previous_package, candidate_root):
            sys.modules.pop(package_name, None)
            removed_package = True
        if previous_module is not None and not _module_belongs_to_root(previous_module, candidate_root):
            sys.modules.pop(module_name, None)
            removed_module = True
        try:
            importlib.invalidate_caches()
            return import_module(module_name)
        except Exception as exc:
            errors.append(exc)
            sys.modules.pop(module_name, None)
            if removed_module and previous_module is not None:
                sys.modules[module_name] = previous_module
            if removed_package and previous_package is not None:
                sys.modules[package_name] = previous_package
        finally:
            if inserted:
                try:
                    sys.path.remove(candidate_str)
                except ValueError:
                    pass

    try:
        return import_module(module_name)
    except Exception as exc:
        errors.append(exc)

    project_root = get_project_root()
    root_hint = f" Current project root hint: {project_root}" if project_root else ""
    raise SmartMonitorBridgeError(
        f"Project bridge module '{module_name}' is not available. "
        f"Set {ENV_PROJECT_ROOT} to the surrounding project root or call "
        f"configure_project_root(...).{root_hint}"
    ) from (errors[-1] if errors else None)
