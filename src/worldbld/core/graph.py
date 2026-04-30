from __future__ import annotations

from typing import Any

from worldbld.core.atom_schemas import CANON_TIERS

DEFAULT_CANON_TIER = "established"


def relationship_records(atom: dict[str, Any]) -> list[dict[str, Any]]:
    atom_id = atom.get("id")
    if not isinstance(atom_id, str) or not atom_id:
        return []

    data = atom.get("data")
    if not isinstance(data, dict):
        return []

    records: list[dict[str, Any]] = []
    relationships = data.get("relationships")
    if not isinstance(relationships, list):
        return records

    for index, rel in enumerate(relationships):
        if not isinstance(rel, dict):
            continue
        predicate = rel.get("predicate")
        obj = rel.get("object")
        if not isinstance(predicate, str) or not predicate.strip():
            continue
        if not isinstance(obj, str) or not obj.strip():
            continue

        subject = rel.get("subject")
        if not isinstance(subject, str) or not subject.strip():
            subject = atom_id

        canon_tier = rel.get("canon_tier")
        if not isinstance(canon_tier, str) or canon_tier not in CANON_TIERS:
            canon_tier = DEFAULT_CANON_TIER

        records.append(
            {
                "id": rel.get("id") if isinstance(rel.get("id"), str) else f"rel.{atom_id}.{index + 1}",
                "subject": subject,
                "predicate": predicate.strip(),
                "object": obj.strip(),
                "summary": rel.get("summary", ""),
                "canon_tier": canon_tier,
                "source": rel.get("source", atom_id),
                "start_date": rel.get("start_date"),
                "end_date": rel.get("end_date"),
                "status": rel.get("status", "active"),
            }
        )

    return records


def timeline_record(atom: dict[str, Any]) -> dict[str, Any] | None:
    if atom.get("type") != "event":
        return None
    atom_id = atom.get("id")
    if not isinstance(atom_id, str) or not atom_id:
        return None

    data = atom.get("data")
    if not isinstance(data, dict):
        return None

    canon_tier = data.get("canon_tier")
    if not isinstance(canon_tier, str) or canon_tier not in CANON_TIERS:
        canon_tier = DEFAULT_CANON_TIER

    return {
        "id": atom_id,
        "name": atom.get("name", ""),
        "summary": atom.get("summary", ""),
        "date_or_era": data.get("date_or_era", ""),
        "participants": data.get("participants", []) if isinstance(data.get("participants"), list) else [],
        "locations": data.get("locations", []) if isinstance(data.get("locations"), list) else [],
        "causes": data.get("causes", []) if isinstance(data.get("causes"), list) else [],
        "consequences": data.get("consequences", []) if isinstance(data.get("consequences"), list) else [],
        "canon_tier": canon_tier,
    }
