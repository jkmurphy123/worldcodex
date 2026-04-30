from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from worldbld.core.atom_schemas import atom_data_template

@dataclass
class AtomEnvelope:
    id: str
    type: str
    name: str
    summary: str = ""
    tags: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None

def atom_stub(atom_id: str, atom_type: str, name: str) -> Dict[str, Any]:
    return {
        "id": atom_id,
        "type": atom_type,
        "name": name,
        "summary": "",
        "tags": [],
        "refs": {},
        "data": atom_data_template(atom_type),
    }
