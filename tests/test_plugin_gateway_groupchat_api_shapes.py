from __future__ import annotations


def test_api_shape_constants_are_compatible_with_reference_routes():
    from api.group_chat import GROUP_CHAT_API_PREFIX
    from api.plugin_center import PLUGIN_ENDPOINTS

    assert GROUP_CHAT_API_PREFIX == "/api/hermes/group-chat"
    assert "/api/hermes/plugins" in PLUGIN_ENDPOINTS
    assert "/api/plugins" in PLUGIN_ENDPOINTS
