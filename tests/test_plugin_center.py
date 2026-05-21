from __future__ import annotations

from pathlib import Path


def test_discover_plugins_normalizes_plugin_yaml(tmp_path: Path):
    from api.plugin_center import discover_plugins

    plugin = tmp_path / "plugins" / "demo_plugin"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text(
        "name: Demo Plugin\ndescription: Test plugin\nversion: 1.2.3\nenabled: true\n",
        encoding="utf-8",
    )

    payload = discover_plugins([tmp_path / "plugins"])

    assert payload["success"] is True
    assert payload["plugins"][0]["key"] == "demo_plugin"
    assert payload["plugins"][0]["name"] == "Demo Plugin"
    assert payload["plugins"][0]["kind"] == "plugin"
    assert payload["plugins"][0]["source"] == "local"
    assert payload["plugins"][0]["effectiveStatus"] == "enabled"
    assert payload["plugins"][0]["description"] == "Test plugin"
    assert payload["plugins"][0]["path"].endswith("demo_plugin")


def test_discover_plugins_handles_skill_md_as_readonly_extension(tmp_path: Path):
    from api.plugin_center import discover_plugins

    skill = tmp_path / "skills" / "demo_skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Skill backed extension\n---\n\n# Demo\n",
        encoding="utf-8",
    )

    payload = discover_plugins([tmp_path / "skills"])

    assert payload["plugins"][0]["key"] == "demo-skill"
    assert payload["plugins"][0]["kind"] == "skill"
    assert payload["plugins"][0]["source"] == "skill"
    assert payload["plugins"][0]["effectiveStatus"] == "readonly"


def test_plugins_payload_includes_empty_list_when_roots_missing(tmp_path: Path):
    from api.plugin_center import discover_plugins

    payload = discover_plugins([tmp_path / "missing"])

    assert payload == {"success": True, "plugins": []}
