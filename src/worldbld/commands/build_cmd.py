from __future__ import annotations
import typer

from worldbld.core.paths import WorldPaths, resolve_world_dir
from worldbld.core.indexer import write_index

def build(world_id_or_path: str) -> None:
    root = resolve_world_dir(world_id_or_path)
    wp = WorldPaths(root=root)
    idx = write_index(wp)
    typer.echo(f"Built index: {wp.index_json} (atoms: {len(idx.get('atoms', []))})")
