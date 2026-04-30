from __future__ import annotations
import re
import typer

from worldbld.core.models import atom_stub
from worldbld.core.paths import WorldPaths, resolve_world_dir
from worldbld.core.io import write_json

def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "untitled"

def add(
    world_id_or_path: str,
    atom_type: str = typer.Argument(..., help="Atom type, e.g. place/org/tech/culture"),
    name: str = typer.Argument(..., help="Human name for the atom"),
    atom_id: str = typer.Option("", "--id", help="Override atom id, e.g. place.argonaut_station"),
    pretty: bool = typer.Option(True, "--pretty/--compact", help="Pretty-print JSON"),
) -> None:
    root = resolve_world_dir(world_id_or_path)
    wp = WorldPaths(root=root)

    if not atom_id:
        atom_id = f"{atom_type}.{_slug(name)}"

    rel_path = wp.atoms_dir / atom_type / f"{_slug(name)}.json"
    if rel_path.exists():
        raise typer.BadParameter(f"Atom file already exists: {rel_path}")

    obj = atom_stub(atom_id=atom_id, atom_type=atom_type, name=name)
    write_json(rel_path, obj, pretty=pretty)
    typer.echo(f"Created {atom_id} -> {rel_path}")
