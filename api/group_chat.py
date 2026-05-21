"""Python-native Group Chat REST/SSE support for her-webui."""
from __future__ import annotations

import json
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from api.config import STATE_DIR
from api.helpers import bad, j
from api.profile_avatar import MENTION_ALIASES, profile_avatar_payload

GROUP_CHAT_API_PREFIX = "/api/hermes/group-chat"
GROUP_CHAT_SSE_POLL_SECONDS = 1.0
_GROUP_CHAT_STATE_FILE = STATE_DIR / "group_chat.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_mentions(content: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for token in re.findall(r"@[A-Za-z0-9_]+", content or ""):
        profile = MENTION_ALIASES.get(token)
        if profile and profile not in seen:
            seen.add(profile)
            result.append(profile)
    return result


class GroupChatStore:
    def __init__(self, path: str | Path = _GROUP_CHAT_STATE_FILE):
        self.path = Path(path)
        self._lock = threading.RLock()

    def _empty(self) -> dict[str, Any]:
        return {"rooms": [], "events": [], "next_event_id": 1}

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("rooms", [])
                data.setdefault("events", [])
                data.setdefault("next_event_id", 1)
                return data
        except Exception:
            pass
        return self._empty()

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _find_room(self, data: dict[str, Any], room_id: str) -> dict[str, Any]:
        for room in data.get("rooms", []):
            if room.get("id") == room_id:
                return room
        raise KeyError(room_id)

    def _event(self, data: dict[str, Any], room_id: str, event_type: str, **payload) -> dict[str, Any]:
        event = {"id": int(data.get("next_event_id") or 1), "room_id": room_id, "type": event_type, "created_at": _now(), **payload}
        data["next_event_id"] = event["id"] + 1
        data.setdefault("events", []).append(event)
        data["events"] = data["events"][-1000:]
        return event

    def list_rooms(self) -> list[dict[str, Any]]:
        with self._lock:
            data = self._load()
            return [{k: v for k, v in room.items() if k != "messages"} | {"message_count": len(room.get("messages", []))} for room in data.get("rooms", [])]

    def create_room(self, name: str, description: str = "") -> dict[str, Any]:
        with self._lock:
            data = self._load()
            room = {
                "id": uuid.uuid4().hex[:12],
                "name": str(name or "Group Chat").strip() or "Group Chat",
                "description": str(description or ""),
                "agents": [],
                "messages": [],
                "created_at": _now(),
                "updated_at": _now(),
            }
            data.setdefault("rooms", []).append(room)
            self._event(data, room["id"], "room_created", room={k: v for k, v in room.items() if k != "messages"})
            self._save(data)
            return room

    def get_room(self, room_id: str) -> dict[str, Any]:
        with self._lock:
            data = self._load()
            return self._find_room(data, room_id)

    def add_agent(self, room_id: str, profile: str) -> dict[str, Any]:
        with self._lock:
            data = self._load()
            room = self._find_room(data, room_id)
            profile = str(profile or "").strip()
            if not profile:
                raise ValueError("profile is required")
            existing = next((a for a in room.get("agents", []) if a.get("profile") == profile), None)
            if existing:
                return existing
            agent = {"profile": profile, "avatar": profile_avatar_payload({"name": profile}), "joined_at": _now()}
            room.setdefault("agents", []).append(agent)
            room["updated_at"] = _now()
            self._event(data, room_id, "agent_added", profile=profile, agent=agent)
            self._save(data)
            return agent

    def remove_agent(self, room_id: str, profile: str) -> bool:
        with self._lock:
            data = self._load()
            room = self._find_room(data, room_id)
            before = len(room.get("agents", []))
            room["agents"] = [a for a in room.get("agents", []) if a.get("profile") != profile]
            changed = len(room["agents"]) != before
            if changed:
                room["updated_at"] = _now()
                self._event(data, room_id, "agent_removed", profile=profile)
                self._save(data)
            return changed

    def add_message(self, room_id: str, role: str, content: str, sender: str = "user") -> dict[str, Any]:
        with self._lock:
            data = self._load()
            room = self._find_room(data, room_id)
            message = {
                "id": uuid.uuid4().hex[:12],
                "role": str(role or "user"),
                "sender": str(sender or "user"),
                "content": str(content or ""),
                "mentions": parse_mentions(str(content or "")),
                "created_at": _now(),
            }
            room.setdefault("messages", []).append(message)
            room["updated_at"] = _now()
            self._event(data, room_id, "message", message=message)
            self._save(data)
            return message

    def fetch_events(self, room_id: str, since: int = 0) -> dict[str, Any]:
        with self._lock:
            data = self._load()
            events = [e for e in data.get("events", []) if e.get("room_id") == room_id and int(e.get("id") or 0) > int(since or 0)]
            cursor = int(since or 0)
            if events:
                cursor = int(events[-1].get("id") or cursor)
            return {"events": events, "cursor": cursor}


_STORE = GroupChatStore()


def _room_id_from_path(path: str) -> str | None:
    suffix = path[len(GROUP_CHAT_API_PREFIX):].strip("/")
    parts = suffix.split("/") if suffix else []
    if len(parts) >= 2 and parts[0] == "rooms":
        return parts[1]
    return None


def handle_group_chat_get(handler, parsed) -> bool:
    path = parsed.path.rstrip("/")
    if not path.startswith(GROUP_CHAT_API_PREFIX):
        return False
    if path == f"{GROUP_CHAT_API_PREFIX}/rooms":
        j(handler, {"success": True, "rooms": _STORE.list_rooms()})
        return True
    if path.endswith("/events/stream"):
        return _handle_group_chat_sse_stream(handler, parsed)
    room_id = _room_id_from_path(path)
    if room_id:
        try:
            j(handler, {"success": True, "room": _STORE.get_room(room_id)})
            return True
        except KeyError:
            bad(handler, "room not found", status=404)
            return True
    return False


def handle_group_chat_post(handler, parsed, body: dict[str, Any]) -> bool:
    path = parsed.path.rstrip("/")
    if not path.startswith(GROUP_CHAT_API_PREFIX):
        return False
    if path == f"{GROUP_CHAT_API_PREFIX}/rooms":
        j(handler, {"success": True, "room": _STORE.create_room(body.get("name") or body.get("title") or "Group Chat", body.get("description") or "")})
        return True
    room_id = _room_id_from_path(path)
    if room_id and path.endswith("/agents"):
        try:
            j(handler, {"success": True, "agent": _STORE.add_agent(room_id, str(body.get("profile") or body.get("name") or ""))})
            return True
        except (KeyError, ValueError) as exc:
            bad(handler, str(exc), status=404 if isinstance(exc, KeyError) else 400)
            return True
    if room_id and path.endswith("/messages"):
        try:
            j(handler, {"success": True, "message": _STORE.add_message(room_id, body.get("role") or "user", body.get("content") or "", body.get("sender") or "user")})
            return True
        except KeyError as exc:
            bad(handler, str(exc), status=404)
            return True
    return False


def handle_group_chat_delete(handler, parsed, body: dict[str, Any] | None = None) -> bool:
    path = parsed.path.rstrip("/")
    if not path.startswith(GROUP_CHAT_API_PREFIX):
        return False
    room_id = _room_id_from_path(path)
    match = re.search(r"/rooms/([^/]+)/agents/([^/]+)$", path)
    if room_id and match:
        removed = _STORE.remove_agent(match.group(1), match.group(2))
        j(handler, {"success": True, "removed": removed})
        return True
    return False


def _sse_write(handler, event: str, data: Any, event_id: int | None = None) -> None:
    # Static contract for tests and EventSource clients: `event: hello`, `event: message`.
    if event_id is not None:
        handler.wfile.write(f"id: {event_id}\n".encode("utf-8"))
    handler.wfile.write(f"event: {event}\n".encode("utf-8"))
    payload = json.dumps(data, ensure_ascii=False)
    for line in payload.splitlines() or [""]:
        handler.wfile.write(f"data: {line}\n".encode("utf-8"))
    handler.wfile.write(b"\n")
    try:
        handler.wfile.flush()
    except Exception:
        pass


def _handle_group_chat_sse_stream(handler, parsed) -> bool:
    room_id = _room_id_from_path(parsed.path.rstrip("/"))
    if not room_id:
        bad(handler, "room_id is required", status=400)
        return True
    qs = parse_qs(parsed.query or "")
    cursor = int((qs.get("cursor") or qs.get("since") or [0])[0] or 0)
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Connection", "keep-alive")
    handler.end_headers()
    _sse_write(handler, "hello", {"room_id": room_id, "cursor": cursor})
    deadline = time.time() + 25
    while time.time() < deadline:
        payload = _STORE.fetch_events(room_id, since=cursor)
        for event in payload["events"]:
            cursor = int(event.get("id") or cursor)
            _sse_write(handler, event.get("type") or "events", event, event_id=cursor)
        if payload["events"]:
            continue
        _sse_write(handler, "heartbeat", {"room_id": room_id, "cursor": cursor})
        time.sleep(GROUP_CHAT_SSE_POLL_SECONDS)
    return True
