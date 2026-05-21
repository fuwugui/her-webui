from __future__ import annotations

from pathlib import Path


def test_group_chat_room_agent_message_and_events(tmp_path: Path):
    from api.group_chat import GroupChatStore, parse_mentions

    store = GroupChatStore(tmp_path / "group_chat.json")
    room = store.create_room("Architecture Review")
    store.add_agent(room["id"], "architect")
    store.add_agent(room["id"], "backend_developer")
    message = store.add_message(room["id"], "user", "请 @architect 和 @backend 看一下", sender="owner")

    detail = store.get_room(room["id"])
    events = store.fetch_events(room["id"], since=0)

    assert [a["profile"] for a in detail["agents"]] == ["architect", "backend_developer"]
    assert detail["messages"][0]["id"] == message["id"]
    assert parse_mentions(message["content"]) == ["architect", "backend_developer"]
    assert [e["type"] for e in events["events"]] == ["room_created", "agent_added", "agent_added", "message"]
    assert events["cursor"] == events["events"][-1]["id"]


def test_group_chat_aliases_do_not_include_developer_alias():
    from api.group_chat import parse_mentions

    assert parse_mentions("@web @pm @test @ui @backend") == [
        "web_developer",
        "product_manager",
        "test_manager",
        "ui_designer",
        "backend_developer",
    ]
    assert parse_mentions("@developer") == []


def test_group_chat_removes_agent_and_records_event(tmp_path: Path):
    from api.group_chat import GroupChatStore

    store = GroupChatStore(tmp_path / "group_chat.json")
    room = store.create_room("Ops")
    store.add_agent(room["id"], "test_manager")
    store.remove_agent(room["id"], "test_manager")

    detail = store.get_room(room["id"])
    events = store.fetch_events(room["id"], since=0)["events"]

    assert detail["agents"] == []
    assert events[-1]["type"] == "agent_removed"
    assert events[-1]["profile"] == "test_manager"
