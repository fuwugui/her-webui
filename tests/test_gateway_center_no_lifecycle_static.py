from __future__ import annotations

from pathlib import Path

GATEWAY_CENTER = (Path(__file__).resolve().parents[1] / "api" / "gateway_center.py")


def test_gateway_center_does_not_shell_out_to_start_or_stop_gateways():
    text = GATEWAY_CENTER.read_text(encoding="utf-8") if GATEWAY_CENTER.exists() else ""
    assert "subprocess" not in text
    assert "gateway start" not in text
    assert "gateway stop" not in text
