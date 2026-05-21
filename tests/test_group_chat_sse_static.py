from __future__ import annotations

from pathlib import Path

GROUP_CHAT = (Path(__file__).resolve().parents[1] / "api" / "group_chat.py")


def test_group_chat_module_defines_sse_stream_handler():
    text = GROUP_CHAT.read_text(encoding="utf-8") if GROUP_CHAT.exists() else ""
    assert "text/event-stream" in text
    assert "event: hello" in text
    assert "event: message" in text or "event: events" in text
    assert "GROUP_CHAT_SSE_POLL_SECONDS" in text
