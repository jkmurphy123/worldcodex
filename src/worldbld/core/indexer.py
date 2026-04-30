from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from worldbld.core.graph import relationship_records, timeline_record
from worldbld.core.io import read_json, write_json
from worldbld.core.paths import WorldPaths

def scan_atoms(atoms_dir: Path) -> List[Path]:
    if not atoms_dir.exists():
        return []
    return sorted(atoms_dir.rglob("*.json"))

def build_index(wp: WorldPaths) -> Dict[str, Any]:
    files = scan_atoms(wp.atoms_dir)
    atoms: List[Dict[str, Any]] = []
    type_map: Dict[str, List[str]] = {}
    tag_map: Dict[str, List[str]] = {}
    id_to_path: Dict[str, str] = {}
    relationships: List[Dict[str, Any]] = []
    relationship_map: Dict[str, List[Dict[str, Any]]] = {}
    timeline: List[Dict[str, Any]] = []

    for f in files:
        try:
            obj = read_json(f)
        except Exception:
            # skip unreadable JSON in v1; later you’ll want `world validate`
            continue

        atom_id = obj.get("id")
        atom_type = obj.get("type")
        if not atom_id or not atom_type:
            continue

        # envelope fields for fast querying
        rec = {
            "id": atom_id,
            "type": atom_type,
            "name": obj.get("name", ""),
            "summary": obj.get("summary", ""),
            "tags": obj.get("tags", []) or [],
            "canon_tier": (obj.get("data") or {}).get("canon_tier", "established") if isinstance(obj.get("data"), dict) else "established",
            "status": (obj.get("data") or {}).get("status", "active") if isinstance(obj.get("data"), dict) else "active",
            "path": str(f.relative_to(wp.root)),
        }
        atoms.append(rec)
        id_to_path[atom_id] = rec["path"]

        type_map.setdefault(atom_type, []).append(atom_id)
        for t in rec["tags"]:
            tag_map.setdefault(t, []).append(atom_id)

        atom_relationships = relationship_records(obj)
        relationships.extend(atom_relationships)
        for rel in atom_relationships:
            relationship_map.setdefault(rel["subject"], []).append(rel)
            relationship_map.setdefault(rel["object"], []).append(rel)

        event = timeline_record(obj)
        if event is not None:
            timeline.append(event)

    timeline.sort(key=lambda item: str(item.get("date_or_era", "")))

    index = {
        "version": 2,
        "atoms": atoms,
        "type_map": type_map,
        "tag_map": tag_map,
        "id_to_path": id_to_path,
        "relationships": relationships,
        "relationship_map": relationship_map,
        "timeline": timeline,
    }
    return index

def write_index(wp: WorldPaths) -> Dict[str, Any]:
    idx = build_index(wp)
    write_json(wp.index_json, idx, pretty=True)
    return idx
