from __future__ import annotations

from pathlib import Path

PROFILES = (Path(__file__).resolve().parents[1] / "api" / "profiles.py").read_text(encoding="utf-8")


def test_profiles_api_includes_avatar_payload():
    assert "profile_avatar_payload" in PROFILES
    assert "'avatar'" in PROFILES or '"avatar"' in PROFILES
