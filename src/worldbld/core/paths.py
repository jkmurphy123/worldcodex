from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class WorldPaths:
    root: Path

    @property
    def world_toml(self) -> Path:
        return self.root / "world.toml"

    @property
    def atoms_dir(self) -> Path:
        return self.root / "atoms"

    @property
    def views_dir(self) -> Path:
        return self.root / "views"

    @property
    def schema_dir(self) -> Path:
        return self.root / "schema"

    @property
    def builds_dir(self) -> Path:
        return self.root / "builds"

    @property
    def exports_dir(self) -> Path:
        return self.builds_dir / "exports"

    @property
    def patches_dir(self) -> Path:
        return self.root / "patches"

    @property
    def index_json(self) -> Path:
        return self.builds_dir / "index.json"

def resolve_world_dir(world_id_or_path: str) -> Path:
    """
    Accept either a world_id (relative folder) or an explicit path.
    For v1, we treat it as a path if it exists or contains a path separator.
    """
    p = Path(world_id_or_path)
    if p.exists() or ("/" in world_id_or_path) or ("\\" in world_id_or_path):
        return p.resolve()
    # default: world lives in ./worlds/<id>
    return (Path.cwd() / "worlds" / world_id_or_path).resolve()
