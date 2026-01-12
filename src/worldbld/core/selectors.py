from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class Selection:
    ids: List[str]

def select_from_index(
    index: Dict[str, Any],
    atom_id: Optional[str] = None,
    atom_type: Optional[str] = None,
    tag: Optional[str] = None,
    id_prefix: Optional[str] = None,
) -> Selection:
    ids: List[str] = []

    if atom_id:
        if atom_id in index.get("id_to_path", {}):
            return Selection(ids=[atom_id])
        return Selection(ids=[])

    # start set: all
    atoms = index.get("atoms", [])
    for rec in atoms:
        if atom_type and rec.get("type") != atom_type:
            continue
        if tag and tag not in (rec.get("tags") or []):
            continue
        if id_prefix and not str(rec.get("id", "")).startswith(id_prefix):
            continue
        ids.append(rec.get("id"))

    return Selection(ids=[i for i in ids if i])
