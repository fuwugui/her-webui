from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
PANELS = (ROOT / "static" / "panels.js").read_text(encoding="utf-8")


def test_static_navigation_contains_new_management_panels():
    assert 'data-panel="plugins"' in INDEX
    assert 'data-panel="gateway"' in INDEX
    assert 'data-panel="groupchat"' in INDEX
    assert 'id="panelPlugins"' in INDEX
    assert 'id="panelGateway"' in INDEX
    assert 'id="panelGroupChat"' in INDEX


def test_panels_js_uses_group_chat_eventsource_and_avatar_renderer():
    assert "EventSource" in PANELS
    assert "/api/hermes/group-chat/rooms/" in PANELS
    assert "events/stream" in PANELS
    assert "renderProfileAvatar" in PANELS
    assert "loadGatewayCenter" in PANELS
    assert "loadPluginCenter" in PANELS
