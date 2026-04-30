from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import shutil
import tempfile
from typing import Any

from worldbld.core.atom_schemas import CANON_TIERS
from worldbld.core.indexer import write_index
from worldbld.core.io import read_json, write_json
from worldbld.core.paths import WorldPaths
from worldbld.core.validation import ValidationIssue, validate_world

PATCH_SCHEMA_VERSION = "worldcodex.patch.v1"

SUPPORTED_OPS = {
    "add_atom",
    "update_atom",
    "deprecate_atom",
    "add_relationship",
    "update_relationship",
    "add_timeline_event",
    "resolve_conflict",
}


@dataclass
class PatchReport:
    patch_path: Path
    world_root: Path
    issues: list[ValidationIssue] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def add_issue(self, path: Path, message: str) -> None:
        self.issues.append(ValidationIssue(path=path, message=message))

    def formatted_issues(self) -> list[str]:
        return [issue.format(self.world_root) for issue in self.issues]


def load_patch(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("Patch payload must be a JSON object")
    return payload


def validate_patch_file(wp: WorldPaths, patch_path: Path) -> PatchReport:
    report = PatchReport(patch_path=patch_path, world_root=wp.root)
    try:
        patch = load_patch(patch_path)
    except Exception as exc:
        report.add_issue(patch_path, f"Invalid patch JSON: {exc}")
        return report
    validate_patch_payload(wp, patch, report)
    return report


def validate_patch_payload(wp: WorldPaths, patch: dict[str, Any], report: PatchReport) -> None:
    if patch.get("schema_version") != PATCH_SCHEMA_VERSION:
        report.add_issue(report.patch_path, f"Patch schema_version must be '{PATCH_SCHEMA_VERSION}'")

    operations = patch.get("operations")
    if not isinstance(operations, list) or not operations:
        report.add_issue(report.patch_path, "Patch must contain a non-empty operations list")
        return

    known_ids = _known_atom_ids(wp)
    added_ids = _added_atom_ids(operations)
    seen_added_ids: set[str] = set()

    for index, operation in enumerate(operations, start=1):
        label = f"operations[{index}]"
        if not isinstance(operation, dict):
            report.add_issue(report.patch_path, f"{label} must be an object")
            continue
        op = operation.get("op")
        if op not in SUPPORTED_OPS:
            report.add_issue(report.patch_path, f"{label}.op must be one of: {', '.join(sorted(SUPPORTED_OPS))}")
            continue

        if op in {"add_atom", "add_timeline_event"}:
            atom = operation.get("atom")
            if not isinstance(atom, dict):
                report.add_issue(report.patch_path, f"{label}.atom must be an object")
                continue
            atom_id = atom.get("id")
            atom_type = atom.get("type")
            if not isinstance(atom_id, str) or not atom_id.strip():
                report.add_issue(report.patch_path, f"{label}.atom.id must be a non-empty string")
                continue
            if atom_id in known_ids or atom_id in seen_added_ids:
                report.add_issue(report.patch_path, f"{label}.atom.id already exists: {atom_id}")
            if op == "add_timeline_event" and atom_type != "event":
                report.add_issue(report.patch_path, f"{label}.atom.type must be 'event'")
            for ref in _references_from_atom(atom):
                if ref not in known_ids and ref not in added_ids:
                    report.add_issue(report.patch_path, f"{label}.atom has missing reference: {ref}")
            seen_added_ids.add(atom_id)
            continue

        if op in {"update_atom", "deprecate_atom", "resolve_conflict"}:
            atom_id = operation.get("atom_id")
            if not _existing_or_added(atom_id, known_ids, added_ids):
                report.add_issue(report.patch_path, f"{label}.atom_id not found: {atom_id}")
            continue

        if op == "add_relationship":
            subject = operation.get("subject")
            obj = operation.get("object")
            predicate = operation.get("predicate")
            if not _existing_or_added(subject, known_ids, added_ids):
                report.add_issue(report.patch_path, f"{label}.subject not found: {subject}")
            if not _existing_or_added(obj, known_ids, added_ids):
                report.add_issue(report.patch_path, f"{label}.object not found: {obj}")
            if not isinstance(predicate, str) or not predicate.strip():
                report.add_issue(report.patch_path, f"{label}.predicate must be a non-empty string")
            canon_tier = operation.get("canon_tier")
            if canon_tier is not None and canon_tier not in CANON_TIERS:
                report.add_issue(report.patch_path, f"{label}.canon_tier must be one of: {', '.join(sorted(CANON_TIERS))}")
            continue

        if op == "update_relationship":
            subject = operation.get("subject")
            obj = operation.get("object")
            predicate = operation.get("predicate")
            if not _existing_or_added(subject, known_ids, added_ids):
                report.add_issue(report.patch_path, f"{label}.subject not found: {subject}")
            if obj is not None and not _existing_or_added(obj, known_ids, added_ids):
                report.add_issue(report.patch_path, f"{label}.object not found: {obj}")
            if not isinstance(predicate, str) or not predicate.strip():
                report.add_issue(report.patch_path, f"{label}.predicate must be a non-empty string")


def preview_patch_file(wp: WorldPaths, patch_path: Path) -> PatchReport:
    report = validate_patch_file(wp, patch_path)
    if not report.ok:
        return report
    patch = load_patch(patch_path)
    for operation in patch["operations"]:
        report.actions.append(_operation_summary(operation))
    return report


def apply_patch_file(wp: WorldPaths, patch_path: Path) -> PatchReport:
    report = preview_patch_file(wp, patch_path)
    if not report.ok:
        return report

    patch = load_patch(patch_path)
    with tempfile.TemporaryDirectory(prefix="worldcodex_patch_") as tmp:
        temp_root = Path(tmp) / wp.root.name
        shutil.copytree(wp.root, temp_root)
        temp_wp = WorldPaths(root=temp_root)
        temp_idx = write_index(temp_wp)
        for operation in patch["operations"]:
            _apply_operation(temp_wp, temp_idx, operation)
            temp_idx = write_index(temp_wp)

        temp_world_report = validate_world(temp_wp)
        if not temp_world_report.ok:
            report.issues.extend(temp_world_report.issues)
            return report

    idx = write_index(wp)
    for operation in patch["operations"]:
        _apply_operation(wp, idx, operation)
        idx = write_index(wp)

    world_report = validate_world(wp)
    if not world_report.ok:
        report.issues.extend(world_report.issues)
        return report

    archive_path = archive_patch(wp, patch_path, patch)
    report.actions.append(f"archive patch -> {archive_path.relative_to(wp.root)}")
    return report


def archive_patch(wp: WorldPaths, patch_path: Path, patch: dict[str, Any]) -> Path:
    patch_id = patch.get("id") if isinstance(patch.get("id"), str) else patch_path.stem
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_id = _slug(patch_id)
    archive_path = wp.patches_dir / "applied" / f"{timestamp}_{safe_id}.json"
    write_json(archive_path, patch, pretty=True)
    return archive_path


def _apply_operation(wp: WorldPaths, index: dict[str, Any], operation: dict[str, Any]) -> None:
    op = operation["op"]
    if op in {"add_atom", "add_timeline_event"}:
        atom = deepcopy(operation["atom"])
        atom_path = _atom_path_for(wp, atom)
        write_json(atom_path, atom, pretty=True)
        return

    if op == "update_atom":
        atom = _load_atom_by_id(wp, index, operation["atom_id"])
        for path, value in (operation.get("set") or {}).items():
            _set_dotted(atom, path, value)
        write_json(_path_for_atom_id(wp, index, operation["atom_id"]), atom, pretty=True)
        return

    if op == "deprecate_atom":
        atom = _load_atom_by_id(wp, index, operation["atom_id"])
        atom.setdefault("data", {})["canon_tier"] = "deprecated"
        write_json(_path_for_atom_id(wp, index, operation["atom_id"]), atom, pretty=True)
        return

    if op == "add_relationship":
        atom = _load_atom_by_id(wp, index, operation["subject"])
        relationship = {
            "predicate": operation["predicate"],
            "object": operation["object"],
        }
        for key in ("summary", "canon_tier", "source", "start_date", "end_date", "status"):
            if key in operation:
                relationship[key] = operation[key]
        atom.setdefault("data", {}).setdefault("relationships", []).append(relationship)
        write_json(_path_for_atom_id(wp, index, operation["subject"]), atom, pretty=True)
        return

    if op == "update_relationship":
        atom = _load_atom_by_id(wp, index, operation["subject"])
        relationships = atom.setdefault("data", {}).setdefault("relationships", [])
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            if rel.get("predicate") != operation["predicate"]:
                continue
            if "object" in operation and rel.get("object") != operation["object"]:
                continue
            for key, value in (operation.get("set") or {}).items():
                rel[key] = value
            break
        write_json(_path_for_atom_id(wp, index, operation["subject"]), atom, pretty=True)
        return

    if op == "resolve_conflict":
        atom = _load_atom_by_id(wp, index, operation["atom_id"])
        data = atom.setdefault("data", {})
        data["status"] = "resolved"
        data["current_state"] = operation.get("resolution", "resolved")
        write_json(_path_for_atom_id(wp, index, operation["atom_id"]), atom, pretty=True)


def _operation_summary(operation: dict[str, Any]) -> str:
    op = operation.get("op")
    if op in {"add_atom", "add_timeline_event"}:
        atom = operation.get("atom", {})
        return f"{op} {atom.get('id')}"
    if op in {"update_atom", "deprecate_atom", "resolve_conflict"}:
        return f"{op} {operation.get('atom_id')}"
    if op in {"add_relationship", "update_relationship"}:
        return f"{op} {operation.get('subject')} -[{operation.get('predicate')}]-> {operation.get('object')}"
    return str(operation)


def _known_atom_ids(wp: WorldPaths) -> set[str]:
    idx = write_index(wp)
    return set(idx.get("id_to_path", {}))


def _added_atom_ids(operations: list[Any]) -> set[str]:
    ids: set[str] = set()
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        if operation.get("op") not in {"add_atom", "add_timeline_event"}:
            continue
        atom = operation.get("atom")
        if isinstance(atom, dict) and isinstance(atom.get("id"), str):
            ids.add(atom["id"])
    return ids


def _references_from_atom(atom: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    data = atom.get("data")
    if not isinstance(data, dict):
        return refs
    for key in ("participants", "locations", "parties"):
        value = data.get(key)
        if isinstance(value, list):
            refs.update(item for item in value if isinstance(item, str) and "." in item)
    relationships = data.get("relationships")
    if isinstance(relationships, list):
        for rel in relationships:
            if isinstance(rel, dict):
                for key in ("subject", "object"):
                    value = rel.get(key)
                    if isinstance(value, str) and "." in value:
                        refs.add(value)
    return refs


def _existing_or_added(value: object, known_ids: set[str], added_ids: set[str]) -> bool:
    return isinstance(value, str) and value in known_ids.union(added_ids)


def _atom_path_for(wp: WorldPaths, atom: dict[str, Any]) -> Path:
    atom_type = str(atom["type"])
    atom_id = str(atom["id"])
    slug = atom_id.split(".", 1)[1] if "." in atom_id else atom_id
    return wp.atoms_dir / atom_type / f"{_slug(slug)}.json"


def _path_for_atom_id(wp: WorldPaths, index: dict[str, Any], atom_id: str) -> Path:
    rel_path = index.get("id_to_path", {}).get(atom_id)
    if not rel_path:
        raise ValueError(f"Atom id not found: {atom_id}")
    return wp.root / rel_path


def _load_atom_by_id(wp: WorldPaths, index: dict[str, Any], atom_id: str) -> dict[str, Any]:
    atom = read_json(_path_for_atom_id(wp, index, atom_id))
    if not isinstance(atom, dict):
        raise ValueError(f"Atom is not an object: {atom_id}")
    return atom


def _set_dotted(obj: dict[str, Any], path: str, value: Any) -> None:
    cur = obj
    parts = path.split(".")
    for part in parts[:-1]:
        child = cur.get(part)
        if not isinstance(child, dict):
            child = {}
            cur[part] = child
        cur = child
    cur[parts[-1]] = value


def _slug(value: str) -> str:
    out = "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    return out or "patch"
