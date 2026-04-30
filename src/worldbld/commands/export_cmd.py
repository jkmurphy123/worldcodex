from __future__ import annotations

from pathlib import Path

import typer

from worldbld.core.atom_schemas import CANON_TIERS
from worldbld.core.exports import EXPORT_TYPES, build_context_export, normalize_export_type
from worldbld.core.indexer import write_index
from worldbld.core.io import print_json, read_json, write_json
from worldbld.core.paths import WorldPaths, resolve_world_dir


def export_context(
    world_id_or_path: str,
    context_type: str = typer.Argument(..., help="Export type, e.g. story-context or news-context"),
    out: Path | None = typer.Option(None, "--out", help="Write export JSON to this path instead of stdout"),
    location: str = typer.Option("", "--location", help="Filter around a place id"),
    character: str = typer.Option("", "--character", help="Filter around a character id"),
    faction: str = typer.Option("", "--faction", help="Filter around an org/faction id"),
    tag: str = typer.Option("", "--tag", help="Filter atoms by tag"),
    canon_tier: str = typer.Option("", "--canon-tier", help="Filter atoms by canon tier"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    normalized_type = normalize_export_type(context_type)
    if normalized_type not in EXPORT_TYPES:
        allowed = ", ".join(sorted(value.replace("_", "-") for value in EXPORT_TYPES))
        raise typer.BadParameter(f"Unknown context type '{context_type}'. Expected one of: {allowed}")
    if canon_tier and canon_tier not in CANON_TIERS:
        raise typer.BadParameter(f"--canon-tier must be one of: {', '.join(sorted(CANON_TIERS))}")

    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    idx = _load_index(wp, rebuild_index)
    payload = build_context_export(
        wp,
        idx,
        normalized_type,
        location_id=location,
        character_id=character,
        faction_id=faction,
        tag=tag,
        canon_tier=canon_tier,
    )

    if out is not None:
        write_json(out, payload, pretty=pretty)
        typer.echo(f"Wrote {normalized_type} export: {out}")
        return

    print_json(payload, pretty=pretty, jsonl=False)


def _load_index(wp: WorldPaths, rebuild_index: bool) -> dict:
    if rebuild_index or not wp.index_json.exists():
        return write_index(wp)
    try:
        return read_json(wp.index_json)
    except Exception:
        return write_index(wp)
