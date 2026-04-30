from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from worldbld.cli import app
from worldbld.core.indexer import write_index
from worldbld.core.io import read_json
from worldbld.core.models import atom_stub
from worldbld.core.patches import apply_patch_file, preview_patch_file, validate_patch_file
from worldbld.core.paths import WorldPaths
from worldbld.core.validation import validate_world


runner = CliRunner()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def make_patch_world(tmp_path: Path) -> Path:
    root = tmp_path / "worlds" / "patch"
    root.mkdir(parents=True)
    (root / "world.toml").write_text('id = "patch"\ntitle = "Patch World"\n', encoding="utf-8")

    place = atom_stub("place.demo_place", "place", "Demo Place")
    place["summary"] = "Demo place summary"
    place["data"]["logline"] = "A demo place."

    character = atom_stub("character.demo_person", "character", "Demo Person")
    character["summary"] = "Demo person summary"
    character["data"]["relationships"] = [{"predicate": "lives_in", "object": "place.demo_place"}]

    conflict = atom_stub("conflict.demo_conflict", "conflict", "Demo Conflict")
    conflict["summary"] = "Demo conflict summary"
    conflict["data"]["parties"] = ["character.demo_person"]
    conflict["data"]["stakes"] = "Whether the patch works."
    conflict["data"]["current_state"] = "unresolved"
    conflict["data"]["escalation_paths"] = ["The patch fails."]
    conflict["data"]["possible_resolutions"] = ["The patch passes."]

    write_json(root / "atoms" / "place" / "demo_place.json", place)
    write_json(root / "atoms" / "character" / "demo_person.json", character)
    write_json(root / "atoms" / "conflict" / "demo_conflict.json", conflict)
    return root


def valid_patch() -> dict:
    event = atom_stub("event.demo_event", "event", "Demo Event")
    event["summary"] = "Demo event summary"
    event["data"]["date_or_era"] = "2200-01-01"
    event["data"]["participants"] = ["character.demo_person"]
    event["data"]["locations"] = ["place.demo_place"]
    event["data"]["causes"] = ["A patch was applied."]
    event["data"]["consequences"] = ["The world changed."]
    return {
        "schema_version": "worldcodex.patch.v1",
        "id": "demo-patch",
        "description": "Patch test",
        "operations": [
            {"op": "add_timeline_event", "atom": event},
            {
                "op": "add_relationship",
                "subject": "character.demo_person",
                "predicate": "witnessed",
                "object": "event.demo_event",
                "summary": "Demo Person witnessed Demo Event.",
            },
            {
                "op": "resolve_conflict",
                "atom_id": "conflict.demo_conflict",
                "resolution": "resolved by test patch",
            },
        ],
    }


def test_validate_patch_accepts_valid_patch(tmp_path: Path) -> None:
    root = make_patch_world(tmp_path)
    patch_path = tmp_path / "patch.json"
    write_json(patch_path, valid_patch())

    report = validate_patch_file(WorldPaths(root=root), patch_path)

    assert report.ok, "\n".join(report.formatted_issues())


def test_preview_patch_does_not_mutate_world(tmp_path: Path) -> None:
    root = make_patch_world(tmp_path)
    patch_path = tmp_path / "patch.json"
    write_json(patch_path, valid_patch())

    report = preview_patch_file(WorldPaths(root=root), patch_path)

    assert report.ok
    assert any("add_timeline_event event.demo_event" in action for action in report.actions)
    assert not (root / "atoms" / "event" / "demo_event.json").exists()


def test_apply_patch_adds_event_relationship_and_archive(tmp_path: Path) -> None:
    root = make_patch_world(tmp_path)
    wp = WorldPaths(root=root)
    patch_path = tmp_path / "patch.json"
    write_json(patch_path, valid_patch())

    report = apply_patch_file(wp, patch_path)

    assert report.ok, "\n".join(report.formatted_issues())
    assert (root / "atoms" / "event" / "demo_event.json").exists()
    character = read_json(root / "atoms" / "character" / "demo_person.json")
    assert any(rel["object"] == "event.demo_event" for rel in character["data"]["relationships"])
    conflict = read_json(root / "atoms" / "conflict" / "demo_conflict.json")
    assert conflict["data"]["status"] == "resolved"
    assert list((root / "patches" / "applied").glob("*.json"))
    assert validate_world(wp).ok
    idx = write_index(wp)
    assert idx["timeline"][0]["id"] == "event.demo_event"


def test_validate_patch_rejects_missing_reference(tmp_path: Path) -> None:
    root = make_patch_world(tmp_path)
    patch = valid_patch()
    patch["operations"][0]["atom"]["data"]["participants"] = ["character.missing"]
    patch_path = tmp_path / "bad_patch.json"
    write_json(patch_path, patch)

    report = validate_patch_file(WorldPaths(root=root), patch_path)

    assert not report.ok
    assert any("missing reference: character.missing" in issue for issue in report.formatted_issues())


def test_patch_cli_apply(tmp_path: Path) -> None:
    root = make_patch_world(tmp_path)
    patch_path = tmp_path / "patch.json"
    write_json(patch_path, valid_patch())

    result = runner.invoke(app, ["patch", "apply", str(root), str(patch_path)])

    assert result.exit_code == 0
    assert "Patch applied" in result.stdout
    assert (root / "atoms" / "event" / "demo_event.json").exists()
