from __future__ import annotations

import typer

from worldbld.core.indexer import write_index
from worldbld.core.io import print_json, read_json
from worldbld.core.paths import WorldPaths, resolve_world_dir

app = typer.Typer(help="Query indexed world graph and timeline data.", no_args_is_help=True)


def _load_index(wp: WorldPaths, rebuild_index: bool) -> dict:
    if rebuild_index or not wp.index_json.exists():
        return write_index(wp)
    try:
        return read_json(wp.index_json)
    except Exception:
        return write_index(wp)


@app.command("relationships")
def relationships(
    world_id_or_path: str,
    atom_id: str = typer.Argument(..., help="Atom id to inspect, e.g. place.argonaut_station"),
    predicate: str = typer.Option("", "--predicate", help="Optional predicate filter"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    idx = _load_index(wp, rebuild_index)
    rows = idx.get("relationship_map", {}).get(atom_id, [])
    if predicate:
        rows = [row for row in rows if row.get("predicate") == predicate]
    print_json(rows, pretty=pretty, jsonl=False)


@app.command("factions-in")
def factions_in(
    world_id_or_path: str,
    place_id: str = typer.Argument(..., help="Place id, e.g. place.argonaut_station"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    idx = _load_index(wp, rebuild_index)
    rows = []
    for rel in idx.get("relationships", []):
        subject = rel.get("subject")
        obj = rel.get("object")
        predicate = rel.get("predicate")
        if obj != place_id and subject != place_id:
            continue
        other = subject if obj == place_id else obj
        atom = _atom_record(idx, other)
        if atom and atom.get("type") in {"org", "faction"}:
            rows.append({"atom": atom, "relationship": rel})
        elif predicate in {"governed_by", "subject_to"} and obj != place_id:
            atom = _atom_record(idx, obj)
            if atom and atom.get("type") in {"org", "faction"}:
                rows.append({"atom": atom, "relationship": rel})
    print_json(rows, pretty=pretty, jsonl=False)


@app.command("characters-for")
def characters_for(
    world_id_or_path: str,
    atom_id: str = typer.Argument(..., help="Faction/org/place id"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    idx = _load_index(wp, rebuild_index)
    rows = []
    for rel in idx.get("relationship_map", {}).get(atom_id, []):
        for candidate in (rel.get("subject"), rel.get("object")):
            atom = _atom_record(idx, candidate)
            if atom and atom.get("type") == "character":
                rows.append({"atom": atom, "relationship": rel})
    print_json(_dedupe_atom_rows(rows), pretty=pretty, jsonl=False)


@app.command("unresolved-conflicts")
def unresolved_conflicts(
    world_id_or_path: str,
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    idx = _load_index(wp, rebuild_index)
    rows = [
        atom
        for atom in idx.get("atoms", [])
        if atom.get("type") == "conflict" and atom.get("status", "active") != "resolved"
    ]
    print_json(rows, pretty=pretty, jsonl=False)


@app.command("events-for")
def events_for(
    world_id_or_path: str,
    atom_id: str = typer.Argument(..., help="Atom id mentioned in event participants or locations"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    idx = _load_index(wp, rebuild_index)
    rows = []
    for event in idx.get("timeline", []):
        if atom_id in event.get("participants", []) or atom_id in event.get("locations", []):
            rows.append(event)
    print_json(rows, pretty=pretty, jsonl=False)


def _atom_record(index: dict, atom_id: object) -> dict | None:
    if not isinstance(atom_id, str):
        return None
    for atom in index.get("atoms", []):
        if atom.get("id") == atom_id:
            return atom
    return None


def _dedupe_atom_rows(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in rows:
        atom_id = row.get("atom", {}).get("id")
        rel_id = row.get("relationship", {}).get("id")
        key = f"{atom_id}:{rel_id}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped
