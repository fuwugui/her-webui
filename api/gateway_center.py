"""Gateway Center aggregation API.

Read-only in the first adaptation phase: do not start or stop gateways here.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from api.helpers import j
from api.profile_avatar import profile_avatar_payload
from api.profiles import list_profiles_api

try:
    from api.agent_health import build_agent_health_payload
except Exception:  # pragma: no cover - standalone fallback
    def build_agent_health_payload() -> dict[str, Any]:
        return {"alive": None, "details": {}, "checked_at": None}


def start_gateway(*_args, **_kwargs):  # compatibility seam for tests/future UI; intentionally unused
    raise NotImplementedError("Gateway Center is read-only in this phase")


def load_gateway_session_identity_map() -> dict[str, dict[str, Any]]:
    try:
        from api.routes import _load_gateway_session_identity_map

        data = _load_gateway_session_identity_map()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _platform_of(session: dict[str, Any]) -> str:
    return str(session.get("platform") or session.get("raw_source") or "").strip()


def gateway_center_payload() -> dict[str, Any]:
    profiles = list_profiles_api()
    health = build_agent_health_payload()
    sessions = load_gateway_session_identity_map()
    by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for session in sessions.values():
        if not isinstance(session, dict):
            continue
        profile = str(session.get("profile") or session.get("target_profile") or session.get("agent_profile") or "default")
        by_profile[profile].append(session)

    enriched = []
    for profile in profiles:
        item = dict(profile)
        name = str(item.get("name") or "default")
        profile_sessions = by_profile.get(name, [])
        platforms = sorted({_platform_of(s) for s in profile_sessions if _platform_of(s)})
        item["avatar"] = item.get("avatar") or profile_avatar_payload(item)
        item["session_count"] = len(profile_sessions)
        item["platforms"] = platforms
        item["health"] = {
            "alive": health.get("alive"),
            "checked_at": health.get("checked_at"),
            "details": health.get("details", {}),
        }
        enriched.append(item)

    return {
        "success": True,
        "summary": {
            "profile_count": len(enriched),
            "running_count": sum(1 for p in enriched if p.get("gateway_running")),
            "session_count": len(sessions),
            "alive": health.get("alive"),
        },
        "profiles": enriched,
        "health": health,
    }


def handle_gateway_center_get(handler, parsed) -> bool:
    if parsed.path != "/api/gateway/center":
        return False
    j(handler, gateway_center_payload())
    return True
