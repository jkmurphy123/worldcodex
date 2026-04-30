from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List
import typer

from worldbld.core.paths import WorldPaths, resolve_world_dir
from worldbld.core.io import read_json, print_json
from worldbld.core.indexer import write_index


def _load_incoming(json_path: Path | None, use_stdin: bool) -> Dict[str, Any]:
    if use_stdin:
        data = sys.stdin.read()
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(f"Failed to parse JSON from stdin: {exc}") from exc
        return obj

    if not json_path:
        raise typer.BadParameter("Provide either --json PATH or --stdin for incoming data")

    if not json_path.exists():
        raise typer.BadParameter(f"JSON file not found: {json_path}")

    return read_json(json_path)


def _apply_patch(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    updated = dict(existing)
    for k, v in incoming.items():
        updated[k] = v
    return updated


def _changed_keys(old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
    sentinel = object()
    keys = set(old.keys()) | set(new.keys())
    return sorted([k for k in keys if old.get(k, sentinel) != new.get(k, sentinel)])


def _atomic_write_json(path: Path, obj: Dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=path.parent, suffix=".tmp", encoding="utf-8"
    ) as tmp:
        if pretty:
            json.dump(obj, tmp, ensure_ascii=False, indent=2)
        else:
            json.dump(obj, tmp, ensure_ascii=False, separators=(",", ":"))
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def update(
    world_id_or_path: str,
    atom_id: str = typer.Argument(..., help="Atom id, e.g. place.hydroponics_ring"),
    json_path: Path | None = typer.Option(
        None, "--json", help="Path to JSON file with patch or replacement object"
    ),
    stdin: bool = typer.Option(False, "--stdin", help="Read JSON from stdin instead of --json"),
    mode: str = typer.Option(
        "patch", "--mode", help="Update mode: patch (shallow merge) or replace"
    ),
    rebuild_index: bool = typer.Option(
        True, "--rebuild-index/--skip-rebuild-index", help="Rebuild index before resolving atom id"
    ),
    build_after: bool = typer.Option(
        True, "--build-after/--skip-build-after", help="Rebuild index after writing update"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show result without writing"),
) -> None:
    root = resolve_world_dir(world_id_or_path)
    wp = WorldPaths(root=root)

    mode = (mode or "").lower()
    if mode not in {"patch", "replace"}:
        raise typer.BadParameter("Mode must be either 'patch' or 'replace'")

    if rebuild_index or (not wp.index_json.exists()):
        idx = write_index(wp)
    else:
        idx = read_json(wp.index_json)

    id_to_path = idx.get("id_to_path", {})
    rel_path = id_to_path.get(atom_id)
    if not rel_path:
        raise typer.BadParameter(f"Atom id not found in index: {atom_id}")

    atom_path = (wp.root / rel_path).resolve()
    if not atom_path.exists():
        raise typer.BadParameter(f"Atom file missing on disk: {atom_path}")

    current = read_json(atom_path)
    if not isinstance(current, dict):
        raise typer.BadParameter(f"Existing atom is not a JSON object: {atom_path}")

    incoming = _load_incoming(json_path=json_path, use_stdin=stdin)
    if not isinstance(incoming, dict):
        raise typer.BadParameter("Incoming JSON must be an object")

    updated = _apply_patch(current, incoming) if mode == "patch" else incoming
    if not isinstance(updated, dict):
        raise typer.BadParameter("Updated content must be a JSON object")

    changed = _changed_keys(current, updated)

    if dry_run:
        typer.echo(f"[DRY-RUN] Would update {atom_id} at {atom_path}")
        typer.echo(f"Mode: {mode}")
        typer.echo(f"Changed keys: {', '.join(changed) if changed else '(none)'}")
        print_json(updated, pretty=True, jsonl=False)
        return

    _atomic_write_json(atom_path, updated, pretty=True)
    typer.echo(
        f"Updated {atom_id} -> {atom_path} (mode={mode}, keys={', '.join(changed) if changed else '(none)'})"
    )

    if build_after:
        idx = write_index(wp)
        typer.echo(f"Rebuilt index: {wp.index_json} (atoms: {len(idx.get('atoms', []))})")


# Manual test steps:
# 1) world init demo --title "Demo World"
# 2) world add demo place "Hydroponics Ring" --id place.hydroponics_ring
# 3) world update demo place.hydroponics_ring --json patch.json --mode patch
# 4) world update demo place.hydroponics_ring --json patch.json --dry-run
