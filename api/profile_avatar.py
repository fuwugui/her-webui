"""Profile avatar normalization for Hermes Web UI.

This module keeps avatar data deterministic and side-effect free so all panels
(Profile, Gateway Center, Group Chat) can render the same profile identity.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

MENTION_ALIASES = {
    "@architect": "architect",
    "@backend_developer": "backend_developer",
    "@backend": "backend_developer",
    "@product_manager": "product_manager",
    "@pm": "product_manager",
    "@test_manager": "test_manager",
    "@test": "test_manager",
    "@ui_designer": "ui_designer",
    "@ui": "ui_designer",
    "@web_developer": "web_developer",
    "@web": "web_developer",
}

_AVATAR_KEYS = ("avatar", "avatar_url", "icon", "photo", "image")


def _safe_name(profile: dict[str, Any] | Any) -> str:
    if isinstance(profile, dict):
        return str(profile.get("name") or profile.get("profile") or "default").strip() or "default"
    return str(getattr(profile, "name", "default") or "default").strip() or "default"


def _initials(name: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", name) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:1].upper()
    return "".join(p[0] for p in parts[:2]).upper()


def _color(name: str) -> str:
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    # Keep colors in a readable mid-range instead of raw hash RGB extremes.
    r = 80 + int(digest[0:2], 16) % 120
    g = 80 + int(digest[2:4], 16) % 120
    b = 80 + int(digest[4:6], 16) % 120
    return f"#{r:02x}{g:02x}{b:02x}"


def _read_profile_config(profile_path: str | Path | None) -> dict[str, Any]:
    if not profile_path:
        return {}
    path = Path(profile_path).expanduser() / "config.yaml"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        # Minimal fallback for the simple `profile:\n  avatar_url: ...` shape.
        result: dict[str, Any] = {}
        current: dict[str, Any] | None = None
        for raw in text.splitlines():
            if not raw.strip() or raw.strip().startswith("#") or ":" not in raw:
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            key, value = raw.strip().split(":", 1)
            value = value.strip().strip('"\'')
            if indent == 0:
                if value:
                    result[key] = value
                    current = None
                else:
                    current = result.setdefault(key, {})
            elif current is not None:
                current[key] = value
        return result


def _configured_avatar(profile: dict[str, Any]) -> tuple[str | None, str | None]:
    url = None
    icon = None
    for key in _AVATAR_KEYS:
        value = profile.get(key)
        if not value:
            continue
        if key == "icon" and not str(value).startswith(("http://", "https://", "/", "data:")):
            icon = str(value)
        else:
            url = str(value)
    cfg = _read_profile_config(profile.get("path"))
    sections = [cfg, cfg.get("profile", {}) if isinstance(cfg.get("profile"), dict) else {}]
    for section in sections:
        for key in _AVATAR_KEYS:
            value = section.get(key) if isinstance(section, dict) else None
            if not value:
                continue
            if key == "icon" and not str(value).startswith(("http://", "https://", "/", "data:")):
                icon = str(value)
            else:
                url = str(value)
    return url, icon


def profile_avatar_payload(profile: dict[str, Any] | Any) -> dict[str, Any]:
    data = profile if isinstance(profile, dict) else vars(profile)
    name = _safe_name(data)
    url, icon = _configured_avatar(data)
    return {
        "initials": _initials(name),
        "color": _color(name),
        "url": url,
        "icon": icon,
        "profile": name,
    }
