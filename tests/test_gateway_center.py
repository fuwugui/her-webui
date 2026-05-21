from __future__ import annotations


def test_gateway_center_payload_aggregates_profiles_without_starting_gateways(monkeypatch):
    from api import gateway_center

    calls = []
    monkeypatch.setattr(
        gateway_center,
        "list_profiles_api",
        lambda: [
            {
                "name": "architect",
                "gateway_running": True,
                "model": "claude-sonnet",
                "provider": "anthropic",
            },
            {
                "name": "backend_developer",
                "gateway_running": False,
                "model": "gpt-5.5",
                "provider": "openai-codex",
            },
        ],
    )
    monkeypatch.setattr(
        gateway_center,
        "build_agent_health_payload",
        lambda: {"alive": True, "details": {"pid": 1234}, "checked_at": "now"},
    )
    monkeypatch.setattr(
        gateway_center,
        "load_gateway_session_identity_map",
        lambda: {
            "s1": {"platform": "telegram", "profile": "architect"},
            "s2": {"platform": "discord", "profile": "backend_developer"},
        },
    )
    monkeypatch.setattr(gateway_center, "start_gateway", lambda *a, **k: calls.append("start"))

    payload = gateway_center.gateway_center_payload()

    assert calls == []
    assert payload["success"] is True
    assert payload["summary"]["profile_count"] == 2
    assert payload["summary"]["running_count"] == 1
    assert payload["summary"]["session_count"] == 2
    assert {p["name"] for p in payload["profiles"]} == {"architect", "backend_developer"}
    assert payload["profiles"][0]["avatar"]["initials"] == "A"
    assert payload["profiles"][1]["avatar"]["initials"] == "BD"


def test_gateway_center_groups_platform_sessions_by_profile(monkeypatch):
    from api import gateway_center

    monkeypatch.setattr(
        gateway_center,
        "list_profiles_api",
        lambda: [{"name": "architect", "gateway_running": True}],
    )
    monkeypatch.setattr(
        gateway_center,
        "build_agent_health_payload",
        lambda: {"alive": None, "details": {}, "checked_at": None},
    )
    monkeypatch.setattr(
        gateway_center,
        "load_gateway_session_identity_map",
        lambda: {
            "a": {"platform": "telegram", "profile": "architect"},
            "b": {"raw_source": "telegram", "profile": "architect"},
            "c": {"platform": "weixin", "profile": "architect"},
        },
    )

    profile = gateway_center.gateway_center_payload()["profiles"][0]

    assert profile["session_count"] == 3
    assert profile["platforms"] == ["telegram", "weixin"]
