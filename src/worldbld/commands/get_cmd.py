from __future__ import annotations
from pathlib import Path
import typer

from worldbld.core.paths import WorldPaths, resolve_world_dir
from worldbld.core.io import read_json, print_json
from worldbld.core.indexer import write_index
from worldbld.core.selectors import select_from_index

def get(
    world_id_or_path: str,
    atom_id: str = typer.Argument("", help="Atom id (optional), e.g. place.argonaut_station"),
    atom_type: str = typer.Option("", "--type", help="Filter by type"),
    tag: str = typer.Option("", "--tag", help="Filter by tag"),
    id_prefix: str = typer.Option("", "--id-prefix", help="Filter by id prefix, e.g. tech."),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    jsonl: bool = typer.Option(False, "--jsonl", help="Output JSON Lines (for lists)"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index", help="Rebuild index before querying"),
) -> None:
    root = resolve_world_dir(world_id_or_path)
    wp = WorldPaths(root=root)

    if rebuild_index or (not wp.index_json.exists()):
        idx = write_index(wp)
    else:
        idx = read_json(wp.index_json)

    sel = select_from_index(
        idx,
        atom_id=atom_id or None,
        atom_type=atom_type or None,
        tag=tag or None,
        id_prefix=id_prefix or None,
    )

    id_to_path = idx.get("id_to_path", {})
    results = []
    for aid in sel.ids:
        rel = id_to_path.get(aid)
        if not rel:
            continue
        results.append(read_json(wp.root / rel))

    # if asking for single id, return object not list
    if atom_id:
        out = results[0] if results else None
    else:
        out = results

    print_json(out, pretty=pretty, jsonl=jsonl)
