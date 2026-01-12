from __future__ import annotations
from pathlib import Path
import typer

from worldbld.core.paths import WorldPaths, resolve_world_dir

def init(world_id_or_path: str, title: str = typer.Option(..., "--title", help="World title")) -> None:
    root = resolve_world_dir(world_id_or_path)
    wp = WorldPaths(root=root)

    wp.root.mkdir(parents=True, exist_ok=True)
    wp.atoms_dir.mkdir(parents=True, exist_ok=True)
    wp.views_dir.mkdir(parents=True, exist_ok=True)
    wp.schema_dir.mkdir(parents=True, exist_ok=True)
    wp.builds_dir.mkdir(parents=True, exist_ok=True)
    wp.exports_dir.mkdir(parents=True, exist_ok=True)

    if not wp.world_toml.exists():
        # keep it dead simple in v1
        content = f'id = "{wp.root.name}"\n' + f'title = "{title}"\n'
        wp.world_toml.write_text(content, encoding="utf-8")

    typer.echo(f"Initialized WorldPack at: {wp.root}")
