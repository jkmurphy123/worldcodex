from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from worldbld.cli import app
from worldbld.core.exports import build_context_export
from worldbld.core.indexer import write_index
from worldbld.core.io import read_json
from worldbld.core.models import atom_stub
from worldbld.core.paths import WorldPaths


runner = CliRunner()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def make_export_world(tmp_path: Path) -> Path:
    root = tmp_path / "worlds" / "export"
    root.mkdir(parents=True)
    (root / "world.toml").write_text('id = "export"\ntitle = "Export World"\n', encoding="utf-8")

    place = atom_stub("place.demo_place", "place", "Demo Place")
    place["summary"] = "Demo place summary"
    place["tags"] = ["demo"]
    place["data"]["logline"] = "A demo place."
    place["data"]["visual_identity"]["materials"] = ["glass"]
    place["data"]["relationships"] = [{"predicate": "governed_by", "object": "org.demo_org"}]
    place["data"]["story_hooks"] = ["A place hook."]

    org = atom_stub("org.demo_org", "org", "Demo Org")
    org["summary"] = "Demo org summary"
    org["tags"] = ["demo"]
    org["data"]["prompt_hooks"] = ["An org hook."]

    character = atom_stub("character.demo_person", "character", "Demo Person")
    character["summary"] = "Demo person summary"
    character["tags"] = ["demo"]
    character["data"]["relationships"] = [
        {"predicate": "member_of", "object": "org.demo_org"},
        {"predicate": "lives_in", "object": "place.demo_place"},
    ]
    character["data"]["story_hooks"] = ["A character hook."]

    event = atom_stub("event.demo_event", "event", "Demo Event")
    event["summary"] = "Demo event summary"
    event["tags"] = ["demo"]
    event["data"]["date_or_era"] = "2200-01-01"
    event["data"]["participants"] = ["character.demo_person", "org.demo_org"]
    event["data"]["locations"] = ["place.demo_place"]
    event["data"]["causes"] = ["A test setup"]
    event["data"]["consequences"] = ["A test result"]

    conflict = atom_stub("conflict.demo_conflict", "conflict", "Demo Conflict")
    conflict["summary"] = "Demo conflict summary"
    conflict["tags"] = ["demo"]
    conflict["data"]["parties"] = ["character.demo_person", "org.demo_org"]
    conflict["data"]["stakes"] = "Control of the test."
    conflict["data"]["current_state"] = "unresolved"
    conflict["data"]["escalation_paths"] = ["The test gets worse."]
    conflict["data"]["possible_resolutions"] = ["The test passes."]

    write_json(root / "atoms" / "place" / "demo_place.json", place)
    write_json(root / "atoms" / "org" / "demo_org.json", org)
    write_json(root / "atoms" / "character" / "demo_person.json", character)
    write_json(root / "atoms" / "event" / "demo_event.json", event)
    write_json(root / "atoms" / "conflict" / "demo_conflict.json", conflict)
    return root


def test_news_context_export_shape(tmp_path: Path) -> None:
    root = make_export_world(tmp_path)
    wp = WorldPaths(root=root)
    idx = write_index(wp)

    payload = build_context_export(wp, idx, "news-context")

    assert payload["metadata"]["schema_version"] == "worldcodex.context.v1"
    assert payload["metadata"]["export_type"] == "news_context"
    assert payload["metadata"]["world_id"] == "export"
    assert payload["places"][0]["id"] == "place.demo_place"
    assert payload["factions"][0]["id"] == "org.demo_org"
    assert payload["characters"][0]["id"] == "character.demo_person"
    assert payload["conflicts"][0]["id"] == "conflict.demo_conflict"
    assert payload["timeline"][0]["id"] == "event.demo_event"


def test_story_context_filtered_by_character_expands_related_atoms(tmp_path: Path) -> None:
    root = make_export_world(tmp_path)
    wp = WorldPaths(root=root)
    idx = write_index(wp)

    payload = build_context_export(wp, idx, "story_context", character_id="character.demo_person")
    source_ids = set(payload["metadata"]["source_atom_ids"])

    assert "character.demo_person" in source_ids
    assert "place.demo_place" in source_ids
    assert "org.demo_org" in source_ids
    assert any(hook["text"] == "A character hook." for hook in payload["story_hooks"])


def test_image_context_filtered_by_location_keeps_visual_data(tmp_path: Path) -> None:
    root = make_export_world(tmp_path)
    wp = WorldPaths(root=root)
    idx = write_index(wp)

    payload = build_context_export(wp, idx, "image-context", location_id="place.demo_place")

    assert payload["places"][0]["visual_identity"]["materials"] == ["glass"]
    assert payload["metadata"]["filters"]["location"] == "place.demo_place"


def test_export_cli_writes_output_file(tmp_path: Path) -> None:
    root = make_export_world(tmp_path)
    out = tmp_path / "news_context.json"

    result = runner.invoke(app, ["export", str(root), "news-context", "--out", str(out)])

    assert result.exit_code == 0
    payload = read_json(out)
    assert payload["metadata"]["export_type"] == "news_context"


def test_export_cli_rejects_unknown_context(tmp_path: Path) -> None:
    root = make_export_world(tmp_path)

    result = runner.invoke(app, ["export", str(root), "bad-context"])

    assert result.exit_code != 0
    assert "Unknown context type" in result.output
