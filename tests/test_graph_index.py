from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from worldbld.cli import app
from worldbld.core.indexer import write_index
from worldbld.core.models import atom_stub
from worldbld.core.paths import WorldPaths
from worldbld.core.validation import validate_world


runner = CliRunner()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def make_graph_world(tmp_path: Path) -> Path:
    root = tmp_path / "worlds" / "graph"
    root.mkdir(parents=True)
    (root / "world.toml").write_text('id = "graph"\ntitle = "Graph"\n', encoding="utf-8")

    place = atom_stub("place.demo_place", "place", "Demo Place")
    place["summary"] = "Demo place summary"
    place["data"]["logline"] = "A demo place."

    org = atom_stub("org.demo_org", "org", "Demo Org")
    org["summary"] = "Demo org summary"
    org["data"]["relationships"] = [{"predicate": "controls", "object": "place.demo_place"}]

    character = atom_stub("character.demo_person", "character", "Demo Person")
    character["summary"] = "Demo person summary"
    character["data"]["relationships"] = [{"predicate": "member_of", "object": "org.demo_org"}]

    event = atom_stub("event.demo_event", "event", "Demo Event")
    event["summary"] = "Demo event summary"
    event["data"]["date_or_era"] = "2200-01-01"
    event["data"]["participants"] = ["character.demo_person", "org.demo_org"]
    event["data"]["locations"] = ["place.demo_place"]
    event["data"]["causes"] = ["A test setup"]
    event["data"]["consequences"] = ["A test result"]

    conflict = atom_stub("conflict.demo_conflict", "conflict", "Demo Conflict")
    conflict["summary"] = "Demo conflict summary"
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


def test_build_index_emits_relationships_and_timeline(tmp_path: Path) -> None:
    root = make_graph_world(tmp_path)

    idx = write_index(WorldPaths(root=root))

    assert idx["version"] == 2
    assert any(
        {
            "subject": "org.demo_org",
            "predicate": "controls",
            "object": "place.demo_place",
        }.items()
        <= rel.items()
        for rel in idx["relationships"]
    )
    assert idx["relationship_map"]["place.demo_place"]
    assert idx["timeline"][0]["id"] == "event.demo_event"
    assert idx["timeline"][0]["participants"] == ["character.demo_person", "org.demo_org"]


def test_query_relationships_returns_atom_graph_edges(tmp_path: Path) -> None:
    root = make_graph_world(tmp_path)

    result = runner.invoke(app, ["query", "relationships", str(root), "org.demo_org"])

    assert result.exit_code == 0
    assert "controls" in result.stdout
    assert "member_of" in result.stdout


def test_query_events_for_returns_timeline_events(tmp_path: Path) -> None:
    root = make_graph_world(tmp_path)

    result = runner.invoke(app, ["query", "events-for", str(root), "character.demo_person"])

    assert result.exit_code == 0
    assert "event.demo_event" in result.stdout


def test_query_unresolved_conflicts_returns_conflict_atoms(tmp_path: Path) -> None:
    root = make_graph_world(tmp_path)

    result = runner.invoke(app, ["query", "unresolved-conflicts", str(root)])

    assert result.exit_code == 0
    assert "conflict.demo_conflict" in result.stdout


def test_validate_reports_bad_relationship_shape(tmp_path: Path) -> None:
    root = make_graph_world(tmp_path)
    character_path = root / "atoms" / "character" / "demo_person.json"
    character = json.loads(character_path.read_text(encoding="utf-8"))
    character["data"]["relationships"] = [{"object": "org.demo_org"}]
    write_json(character_path, character)

    report = validate_world(WorldPaths(root=root))

    assert not report.ok
    assert any("predicate must be a non-empty string" in issue for issue in report.formatted_issues())


def test_validate_reports_bad_canon_tier(tmp_path: Path) -> None:
    root = make_graph_world(tmp_path)
    event_path = root / "atoms" / "event" / "demo_event.json"
    event = json.loads(event_path.read_text(encoding="utf-8"))
    event["data"]["canon_tier"] = "maybe"
    write_json(event_path, event)

    report = validate_world(WorldPaths(root=root))

    assert not report.ok
    assert any("data.canon_tier" in issue and "must be one of" in issue for issue in report.formatted_issues())
