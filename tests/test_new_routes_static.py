from __future__ import annotations

from pathlib import Path

ROUTES = (Path(__file__).resolve().parents[1] / "api" / "routes.py").read_text(encoding="utf-8")


def test_routes_register_new_extension_gateway_group_chat_endpoints():
    assert "handle_plugin_center_get" in ROUTES
    assert "handle_gateway_center_get" in ROUTES
    assert "handle_group_chat_get" in ROUTES
    assert "handle_group_chat_post" in ROUTES
    assert "handle_group_chat_delete" in ROUTES
    assert "/api/hermes/plugins" in ROUTES
    assert "/api/gateway/center" in ROUTES
    assert "/api/hermes/group-chat" in ROUTES
