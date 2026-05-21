"""Read-only Hermes plugin discovery for the Python/vanilla Web UI."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable

from api.config import HOME
from api.helpers import j

PLUGIN_ENDPOINTS = ("/api/hermes/plugins", "/api/plugins")


def _parse_yaml_like(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        data: dict[str, Any] = {}
        in_frontmatter = text.startswith("---")
        for raw in text.splitlines()[1 if in_frontmatter else 0:]:
            line = raw.strip()
            if in_frontmatter and line == "---":
                break
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"\'')
        return data


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return value or "plugin"


def _plugin_from_dir(path: Path) -> dict[str, Any] | None:
    plugin_yaml = next((path / name for name in ("plugin.yaml", "plugin.yml") if (path / name).exists()), None)
    skill_md = path / "SKILL.md"
    if plugin_yaml:
        meta = _parse_yaml_like(plugin_yaml)
        key = _slug(str(meta.get("key") or meta.get("id") or path.name))
        enabled = meta.get("enabled", True)
        return {
            "key": key,
            "name": str(meta.get("name") or key),
            "kind": "plugin",
            "source": "local",
            "effectiveStatus": "enabled" if enabled is not False and str(enabled).lower() != "false" else "disabled",
            "path": str(path),
            "description": str(meta.get("description") or ""),
            "version": meta.get("version"),
        }
    if skill_md.exists():
        meta = _parse_yaml_like(skill_md)
        key = _slug(str(meta.get("name") or path.name))
        return {
            "key": key,
            "name": str(meta.get("name") or key),
            "kind": "skill",
            "source": "skill",
            "effectiveStatus": "readonly",
            "path": str(path),
            "description": str(meta.get("description") or ""),
            "version": meta.get("version"),
        }
    return None


def default_plugin_roots() -> list[Path]:
    hermes_home = Path(os.getenv("HERMES_HOME", str(HOME / ".hermes"))).expanduser()
    return [
        hermes_home / "plugins",
        hermes_home / "skills",
        Path(__file__).resolve().parents[1] / "plugins",
    ]


def discover_plugins(roots: Iterable[str | Path] | None = None) -> dict[str, Any]:
    plugins: list[dict[str, Any]] = []
    for root in roots or default_plugin_roots():
        base = Path(root).expanduser()
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            item = _plugin_from_dir(child)
            if item:
                plugins.append(item)
    return {"success": True, "plugins": plugins}


def handle_plugin_center_get(handler, parsed) -> bool:
    if parsed.path not in PLUGIN_ENDPOINTS:
        return False
    j(handler, discover_plugins())
    return True
