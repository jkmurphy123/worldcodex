from __future__ import annotations
from typing import Any, Dict, List, Optional

from worldbld.core.io import read_json
from worldbld.core.paths import WorldPaths
from worldbld.core.selectors import select_from_index

def _get_by_path(obj: Any, path: str) -> Any:
    """
    Minimal dotted-path getter: "data.location.body"
    """
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur

def run_view(wp: WorldPaths, index: Dict[str, Any], view_path) -> Any:
    """
    v1 view runner: supports query.include rules + assemble.object with:
      - {"from_atom": "<id>", "path": "<dotted>"}
      - {"from_query": {...}, "map": {"pick": [fields...]}}
    """
    view = read_json(view_path)
    include_rules = view.get("query", {}).get("include", [])

    # Resolve included IDs
    included_ids: List[str] = []
    for rule in include_rules:
        if "id" in rule:
            included_ids.extend(select_from_index(index, atom_id=rule["id"]).ids)
        else:
            included_ids.extend(
                select_from_index(
                    index,
                    atom_type=rule.get("type"),
                    tag=(rule.get("tags_any") or [None])[0] if rule.get("tags_any") else None,
                    id_prefix=rule.get("id_prefix"),
                ).ids
            )
    # unique, stable order
    included_ids = list(dict.fromkeys(included_ids))

    # load atoms
    atoms_by_id: Dict[str, Any] = {}
    id_to_path = index.get("id_to_path", {})
    for aid in included_ids:
        rel = id_to_path.get(aid)
        if not rel:
            continue
        atoms_by_id[aid] = read_json(wp.root / rel)

    assemble = view.get("assemble", {})
    obj_spec = assemble.get("object", {})

    def pick_fields(a: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for f in fields:
            if "." in f:
                out[f] = _get_by_path(a, f)
            else:
                out[f] = a.get(f)
        return out

    def build_object_from_fields(a: Dict[str, Any], fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for spec in fields:
            out_key = spec["out"]
            if "literal" in spec:
                out[out_key] = spec["literal"]
                continue
            val = _get_by_path(a, spec.get("path", "")) if spec.get("path") else None
            if val is None and "default" in spec:
                val = spec["default"]
            out[out_key] = val
        return out

    out_obj: Dict[str, Any] = {}
    for k, spec in obj_spec.items():
        if isinstance(spec, dict) and "from_atom" in spec:
            a = atoms_by_id.get(spec["from_atom"])
            out_obj[k] = _get_by_path(a, spec.get("path", "")) if a else None
        elif isinstance(spec, dict) and "from_query" in spec:
            q = spec["from_query"]
            sel = select_from_index(index, atom_type=q.get("type"), tag=q.get("tag"), id_prefix=q.get("id_prefix"))
            rows = []
            for aid in sel.ids:
                a = atoms_by_id.get(aid) or (read_json(wp.root / id_to_path[aid]) if aid in id_to_path else None)
                if not a:
                    continue
                rows.append(a)
            m = spec.get("map", {})
            if "fields" in m:
                out_obj[k] = [build_object_from_fields(a, m["fields"]) for a in rows]
            else:
                picks = m.get("pick", [])
                out_obj[k] = [pick_fields(a, picks) for a in rows] if picks else rows
        elif isinstance(spec, dict) and "literal" in spec:
            out_obj[k] = spec["literal"]
        else:
            out_obj[k] = spec

    # allow returning whole object/list later; for now only object format
    return out_obj
