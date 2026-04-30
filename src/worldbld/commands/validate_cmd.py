from __future__ import annotations

import typer

from worldbld.core.paths import WorldPaths, resolve_world_dir
from worldbld.core.validation import validate_world


def validate(world_id_or_path: str) -> None:
    root = resolve_world_dir(world_id_or_path)
    report = validate_world(WorldPaths(root=root))

    if report.ok:
        typer.echo(f"World validation passed: {root}")
        return

    typer.echo(f"World validation failed: {root}", err=True)
    for issue in report.formatted_issues():
        typer.echo(f"- {issue}", err=True)
    raise typer.Exit(code=1)
