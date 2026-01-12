from __future__ import annotations
from pathlib import Path
import typer

from worldbld.core.paths import WorldPaths, resolve_world_dir
from worldbld.core.io import read_json, print_json
from worldbld.core.indexer import write_index
from worldbld.core.views import run_view

view_app = typer.Typer(help="Run saved views (query + assemble) to produce exportable JSON.", no_args_is_help=True)

@view_app.command("run")
def view_run(
    world_id_or_path: str,
    view_file: str = typer.Argument(..., help="Path to view JSON (relative to world root or absolute)"),
    pretty: bool = typer.Option(True, "--pretty/--compact"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    root = resolve_world_dir(world_id_or_path)
    wp = WorldPaths(root=root)

    if rebuild_index or (not wp.index_json.exists()):
        idx = write_index(wp)
    else:
        idx = read_json(wp.index_json)

    vpath = Path(view_file)
    if not vpath.is_absolute():
        vpath = (wp.root / view_file).resolve()
    if not vpath.exists():
        raise typer.BadParameter(f"View file not found: {vpath}")

    out = run_view(wp, idx, vpath)
    print_json(out, pretty=pretty, jsonl=False)
