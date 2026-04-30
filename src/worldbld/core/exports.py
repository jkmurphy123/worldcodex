from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worldbld.core.io import read_json
from worldbld.core.paths import WorldPaths

EXPORT_SCHEMA_VERSION = "worldcodex.context.v1"
EXPORT_TYPES = {
    "world_bible",
    "story_context",
    "news_context",
    "image_context",
    "character_context",
    "location_context",
}


def normalize_export_type(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def build_context_export(
    wp: WorldPaths,
    index: dict[str, Any],
    export_type: str,
    *,
    location_id: str = "",
    character_id: str = "",
    faction_id: str = "",
    tag: str = "",
    canon_tier: str = "",
) -> dict[str, Any]:
    normalized_type = normalize_export_type(export_type)
    if normalized_type not in EXPORT_TYPES:
        raise ValueError(f"Unknown export type: {export_type}")

    atoms = _load_atoms(wp, index)
    filters = {
        "location": location_id or None,
        "character": character_id or None,
        "faction": faction_id or None,
        "tag": tag or None,
        "canon_tier": canon_tier or None,
    }
    selected_atoms = _apply_filters(
        atoms,
        index=index,
        location_id=location_id,
        character_id=character_id,
        faction_id=faction_id,
        tag=tag,
        canon_tier=canon_tier,
    )
    selected_ids = {atom["id"] for atom in selected_atoms if isinstance(atom.get("id"), str)}

    relationships = [
        rel
        for rel in index.get("relationships", [])
        if rel.get("subject") in selected_ids or rel.get("object") in selected_ids
    ]
    timeline = [
        event
        for event in index.get("timeline", [])
        if not selected_ids
        or selected_ids.intersection(event.get("participants", []))
        or selected_ids.intersection(event.get("locations", []))
    ]

    payload: dict[str, Any] = {
        "metadata": _metadata(wp, normalized_type, selected_ids, filters),
        "relationships": relationships,
        "timeline": timeline,
    }

    if normalized_type == "world_bible":
        payload["atoms_by_type"] = _group_atoms(selected_atoms)
    elif normalized_type == "news_context":
        payload.update(
            {
                "places": _atoms_of_type(selected_atoms, "place"),
                "factions": _atoms_of_types(selected_atoms, {"org", "faction"}),
                "characters": _atoms_of_type(selected_atoms, "character"),
                "conflicts": _atoms_of_type(selected_atoms, "conflict"),
                "open_threads": _atoms_of_type(selected_atoms, "conflict"),
            }
        )
    elif normalized_type == "story_context":
        payload.update(
            {
                "places": _atoms_of_type(selected_atoms, "place"),
                "characters": _atoms_of_type(selected_atoms, "character"),
                "factions": _atoms_of_types(selected_atoms, {"org", "faction"}),
                "conflicts": _atoms_of_type(selected_atoms, "conflict"),
                "story_hooks": _collect_hooks(selected_atoms),
            }
        )
    elif normalized_type == "image_context":
        payload.update(
            {
                "places": [_image_atom(atom) for atom in _atoms_of_type(selected_atoms, "place")],
                "cultures": [_image_atom(atom) for atom in _atoms_of_type(selected_atoms, "culture")],
                "technologies": [_image_atom(atom) for atom in _atoms_of_type(selected_atoms, "tech")],
                "artifacts": [_image_atom(atom) for atom in _atoms_of_type(selected_atoms, "artifact")],
                "visual_constraints": _collect_visual_constraints(selected_atoms),
            }
        )
    elif normalized_type == "character_context":
        payload.update(
            {
                "characters": _atoms_of_type(selected_atoms, "character"),
                "places": _atoms_of_type(selected_atoms, "place"),
                "factions": _atoms_of_types(selected_atoms, {"org", "faction"}),
                "conflicts": _atoms_of_type(selected_atoms, "conflict"),
            }
        )
    elif normalized_type == "location_context":
        payload.update(
            {
                "places": _atoms_of_type(selected_atoms, "place"),
                "characters": _atoms_of_type(selected_atoms, "character"),
                "factions": _atoms_of_types(selected_atoms, {"org", "faction"}),
                "conflicts": _atoms_of_type(selected_atoms, "conflict"),
                "location_hooks": _collect_hooks(_atoms_of_type(selected_atoms, "place")),
            }
        )

    return payload


def _metadata(
    wp: WorldPaths,
    export_type: str,
    source_atom_ids: set[str],
    filters: dict[str, str | None],
) -> dict[str, Any]:
    world_info = _read_world_info(wp)
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "export_type": export_type,
        "world_id": world_info.get("id") or wp.root.name,
        "world_title": world_info.get("title") or wp.root.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_atom_ids": sorted(source_atom_ids),
        "filters": filters,
    }


def _read_world_info(wp: WorldPaths) -> dict[str, str]:
    if not wp.world_toml.exists():
        return {}
    info: dict[str, str] = {}
    for line in wp.world_toml.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip().strip('"')
        if key in {"id", "title"}:
            info[key] = value
    return info


def _load_atoms(wp: WorldPaths, index: dict[str, Any]) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    for atom_id in sorted(index.get("id_to_path", {})):
        rel_path = index["id_to_path"][atom_id]
        atom = read_json(wp.root / rel_path)
        if isinstance(atom, dict):
            atoms.append(atom)
    return atoms


def _apply_filters(
    atoms: list[dict[str, Any]],
    *,
    index: dict[str, Any],
    location_id: str,
    character_id: str,
    faction_id: str,
    tag: str,
    canon_tier: str,
) -> list[dict[str, Any]]:
    selected_ids = _seed_ids(index, location_id=location_id, character_id=character_id, faction_id=faction_id)
    if selected_ids:
        selected_ids = _expand_related_ids(index, selected_ids)

    rows = atoms
    if selected_ids:
        rows = [atom for atom in rows if atom.get("id") in selected_ids]
    if tag:
        rows = [atom for atom in rows if tag in (atom.get("tags") or [])]
    if canon_tier:
        rows = [atom for atom in rows if _atom_canon_tier(atom) == canon_tier]
    return rows


def _seed_ids(index: dict[str, Any], *, location_id: str, character_id: str, faction_id: str) -> set[str]:
    valid_ids = set(index.get("id_to_path", {}))
    seeds = {value for value in (location_id, character_id, faction_id) if value}
    return {seed for seed in seeds if seed in valid_ids}


def _expand_related_ids(index: dict[str, Any], seeds: set[str]) -> set[str]:
    selected = set(seeds)
    for seed in list(seeds):
        for rel in index.get("relationship_map", {}).get(seed, []):
            subject = rel.get("subject")
            obj = rel.get("object")
            if isinstance(subject, str):
                selected.add(subject)
            if isinstance(obj, str):
                selected.add(obj)
        for event in index.get("timeline", []):
            if seed in event.get("participants", []) or seed in event.get("locations", []):
                selected.add(event.get("id"))
                selected.update(item for item in event.get("participants", []) if isinstance(item, str))
                selected.update(item for item in event.get("locations", []) if isinstance(item, str))
    return selected


def _atom_canon_tier(atom: dict[str, Any]) -> str:
    data = atom.get("data")
    if isinstance(data, dict) and isinstance(data.get("canon_tier"), str):
        return data["canon_tier"]
    return "established"


def _group_atoms(atoms: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for atom in atoms:
        grouped.setdefault(str(atom.get("type", "unknown")), []).append(atom)
    return grouped


def _atoms_of_type(atoms: list[dict[str, Any]], atom_type: str) -> list[dict[str, Any]]:
    return [atom for atom in atoms if atom.get("type") == atom_type]


def _atoms_of_types(atoms: list[dict[str, Any]], atom_types: set[str]) -> list[dict[str, Any]]:
    return [atom for atom in atoms if atom.get("type") in atom_types]


def _collect_hooks(atoms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hooks: list[dict[str, Any]] = []
    for atom in atoms:
        data = atom.get("data")
        if not isinstance(data, dict):
            continue
        values = data.get("story_hooks") or data.get("prompt_hooks") or []
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str) and value.strip():
                    hooks.append({"atom_id": atom.get("id"), "text": value})
    return hooks


def _image_atom(atom: dict[str, Any]) -> dict[str, Any]:
    data = atom.get("data") if isinstance(atom.get("data"), dict) else {}
    return {
        "id": atom.get("id"),
        "type": atom.get("type"),
        "name": atom.get("name"),
        "summary": atom.get("summary"),
        "tags": atom.get("tags", []),
        "visual_identity": data.get("visual_identity", {}),
        "tone": data.get("tone", {}),
        "prompt_hooks": data.get("prompt_hooks", data.get("story_hooks", [])),
        "constraints": data.get("constraints", {}),
    }


def _collect_visual_constraints(atoms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for atom in atoms:
        data = atom.get("data")
        if not isinstance(data, dict):
            continue
        constraints = data.get("constraints") or data.get("tone", {}).get("avoid")
        if constraints:
            rows.append({"atom_id": atom.get("id"), "constraints": constraints})
    return rows
