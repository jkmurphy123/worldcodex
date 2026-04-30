from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from worldbld.cli import app
from worldbld.core.paths import WorldPaths
from worldbld.core.validation import validate_world


runner = CliRunner()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def valid_atom(atom_id: str, atom_type: str, name: str) -> dict:
    return {
        "id": atom_id,
        "type": atom_type,
        "name": name,
        "summary": f"{name} summary",
        "tags": [],
        "refs": {},
        "data": {},
    }


def make_world(tmp_path: Path) -> Path:
    root = tmp_path / "worlds" / "demo"
    root.mkdir(parents=True)
    (root / "world.toml").write_text('id = "demo"\ntitle = "Demo"\n', encoding="utf-8")
    write_json(root / "atoms" / "place" / "demo_place.json", valid_atom("place.demo_place", "place", "Demo Place"))
    return root


def test_validate_world_accepts_valid_world(tmp_path: Path) -> None:
    root = make_world(tmp_path)

    report = validate_world(WorldPaths(root=root))

    assert report.ok


def test_validate_cli_returns_zero_for_valid_world(tmp_path: Path) -> None:
    root = make_world(tmp_path)

    result = runner.invoke(app, ["validate", str(root)])

    assert result.exit_code == 0
    assert "World validation passed" in result.stdout


def test_validate_world_reports_duplicate_ids(tmp_path: Path) -> None:
    root = make_world(tmp_path)
    write_json(
        root / "atoms" / "place" / "duplicate.json",
        valid_atom("place.demo_place", "place", "Duplicate Place"),
    )

    report = validate_world(WorldPaths(root=root))

    assert not report.ok
    assert any("Duplicate id 'place.demo_place'" in issue for issue in report.formatted_issues())


def test_validate_world_reports_broken_relationship_reference(tmp_path: Path) -> None:
    root = make_world(tmp_path)
    atom_path = root / "atoms" / "character" / "demo_character.json"
    atom = valid_atom("character.demo_character", "character", "Demo Character")
    atom["data"]["relationships"] = [{"predicate": "lives_in", "object": "place.missing"}]
    write_json(atom_path, atom)

    report = validate_world(WorldPaths(root=root))

    assert not report.ok
    assert any("Broken reference 'place.missing'" in issue for issue in report.formatted_issues())


def test_validate_world_reports_invalid_json(tmp_path: Path) -> None:
    root = make_world(tmp_path)
    bad_path = root / "views" / "bad.view.json"
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    bad_path.write_text("{not json", encoding="utf-8")

    report = validate_world(WorldPaths(root=root))

    assert not report.ok
    assert any("Invalid JSON" in issue and "bad.view.json" in issue for issue in report.formatted_issues())


def test_sample_world_validates() -> None:
    sample = Path(__file__).resolve().parents[1] / "worlds" / "titan-osa"
    report = validate_world(WorldPaths(root=sample))

    assert report.ok, "\n".join(report.formatted_issues())


def test_sample_world_copy_cli_validates_from_path(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "worlds" / "titan-osa"
    copied = tmp_path / "titan-osa"
    shutil.copytree(source, copied)

    result = runner.invoke(app, ["validate", str(copied)])

    assert result.exit_code == 0
