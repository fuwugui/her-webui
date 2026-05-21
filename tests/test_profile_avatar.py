from __future__ import annotations

from pathlib import Path


def test_profile_avatar_generates_stable_initials_and_color():
    from api.profile_avatar import profile_avatar_payload

    avatar1 = profile_avatar_payload({"name": "backend_developer"})
    avatar2 = profile_avatar_payload({"name": "backend_developer"})

    assert avatar1["initials"] == "BD"
    assert avatar1["color"].startswith("#")
    assert len(avatar1["color"]) == 7
    assert avatar1["color"] == avatar2["color"]
    assert avatar1["url"] is None


def test_profile_avatar_prefers_configured_avatar_url(tmp_path: Path):
    from api.profile_avatar import profile_avatar_payload

    profile_dir = tmp_path / "architect"
    profile_dir.mkdir()
    (profile_dir / "config.yaml").write_text(
        "profile:\n  avatar_url: https://example.test/avatar.png\n",
        encoding="utf-8",
    )

    avatar = profile_avatar_payload({"name": "architect", "path": str(profile_dir)})

    assert avatar["initials"] == "A"
    assert avatar["url"] == "https://example.test/avatar.png"


def test_profile_avatar_supports_icon_and_short_aliases_without_backend_developer_alias():
    from api.profile_avatar import MENTION_ALIASES, profile_avatar_payload

    avatar = profile_avatar_payload({"name": "web_developer", "icon": "🕸️"})

    assert avatar["initials"] == "WD"
    assert avatar["icon"] == "🕸️"
    assert MENTION_ALIASES["@web"] == "web_developer"
    assert MENTION_ALIASES["@backend"] == "backend_developer"
    assert "@developer" not in MENTION_ALIASES
