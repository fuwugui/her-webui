from __future__ import annotations

from pathlib import Path

PLAN = (Path(__file__).resolve().parents[1] / ".hermes" / "plans" / "her-webui-extension-gateway-group-terminal-adaptation.md").read_text(encoding="utf-8")


def test_plan_captures_realtime_group_chat_and_profile_avatars():
    assert "Group Chat（必须实时推送）" in PLAN
    assert "SSE" in PLAN
    assert "Profile 头像" in PLAN
    assert "不引入 Node/Vue/React/Socket.IO" in PLAN
