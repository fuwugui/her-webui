from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
PANELS = (ROOT / "static" / "panels.js").read_text(encoding="utf-8")


def test_terminal_entry_remains_python_pty_backed_and_visible_from_management_ui():
    assert "static/terminal.js" in INDEX or "terminal.js" in INDEX
    assert "/api/terminal" in (ROOT / "api" / "terminal.py").read_text(encoding="utf-8")
    assert "openTerminal" in PANELS or "terminal" in INDEX.lower()
