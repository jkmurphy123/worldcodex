from __future__ import annotations

from pathlib import Path

import typer

from worldbld.core.patches import apply_patch_file, preview_patch_file, validate_patch_file
from worldbld.core.paths import WorldPaths, resolve_world_dir

app = typer.Typer(help="Validate, preview, and apply WorldCodex patch files.", no_args_is_help=True)


@app.command("validate")
def validate_patch(world_id_or_path: str, patch_file: Path) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    report = validate_patch_file(wp, patch_file)
    _finish_report(report, success=f"Patch validation passed: {patch_file}")


@app.command("preview")
def preview_patch(world_id_or_path: str, patch_file: Path) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    report = preview_patch_file(wp, patch_file)
    _finish_report(report, success=f"Patch preview: {patch_file}", show_actions=True)


@app.command("apply")
def apply_patch(world_id_or_path: str, patch_file: Path) -> None:
    wp = WorldPaths(root=resolve_world_dir(world_id_or_path))
    report = apply_patch_file(wp, patch_file)
    _finish_report(report, success=f"Patch applied: {patch_file}", show_actions=True)


def _finish_report(report, *, success: str, show_actions: bool = False) -> None:
    if not report.ok:
        typer.echo("Patch failed:", err=True)
        for issue in report.formatted_issues():
            typer.echo(f"- {issue}", err=True)
        raise typer.Exit(code=1)

    typer.echo(success)
    if show_actions:
        for action in report.actions:
            typer.echo(f"- {action}")
