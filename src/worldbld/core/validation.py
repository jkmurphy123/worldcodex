from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from worldbld.core.atom_schemas import CANON_TIERS, expected_type_name, get_path, schema_for
from worldbld.core.io import read_json
from worldbld.core.indexer import scan_atoms
from worldbld.core.paths import WorldPaths

REQUIRED_ENVELOPE_FIELDS = ("id", "type", "name", "summary", "tags", "refs", "data")


@dataclass
class ValidationIssue:
    path: Path
    message: str

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"{rel}: {self.message}"


@dataclass
class ValidationReport:
    root: Path
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, path: Path, message: str) -> None:
        self.issues.append(ValidationIssue(path=path, message=message))

    def formatted_issues(self) -> list[str]:
        return [issue.format(self.root) for issue in self.issues]


def validate_world(wp: WorldPaths) -> ValidationReport:
    report = ValidationReport(root=wp.root)

    if not wp.root.exists():
        report.add(wp.root, "World directory does not exist")
        return report
    if not wp.root.is_dir():
        report.add(wp.root, "World path is not a directory")
        return report
    if not wp.world_toml.exists():
        report.add(wp.world_toml, "Missing world.toml")

    _validate_json_files(report, wp)

    atom_records = _load_atom_like_records(report, scan_atoms(wp.atoms_dir), required_envelope=True)
    doc_records = _load_atom_like_records(report, _json_files(wp.root / "docs"), required_envelope=False)

    records = [*atom_records, *doc_records]
    id_to_path: dict[str, Path] = {}
    for record in records:
        atom_id = record.obj.get("id")
        if not isinstance(atom_id, str) or not atom_id.strip():
            continue
        if atom_id in id_to_path:
            report.add(record.path, f"Duplicate id '{atom_id}' also found at {id_to_path[atom_id].relative_to(wp.root)}")
        else:
            id_to_path[atom_id] = record.path

    for record in atom_records:
        _validate_atom_envelope(report, wp, record)
        _validate_atom_path_convention(report, wp, record)
        _validate_type_schema(report, record)

    for record in doc_records:
        _validate_type_schema(report, record)

    for record in records:
        _validate_references(report, wp, record, known_ids=set(id_to_path))

    return report


@dataclass
class _Record:
    path: Path
    obj: dict[str, Any]


def _json_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.json"))


def _validate_json_files(report: ValidationReport, wp: WorldPaths) -> None:
    for base in (wp.atoms_dir, wp.views_dir, wp.root / "docs"):
        for path in _json_files(base):
            try:
                read_json(path)
            except Exception as exc:
                report.add(path, f"Invalid JSON: {exc}")


def _load_atom_like_records(
    report: ValidationReport,
    paths: Iterable[Path],
    *,
    required_envelope: bool,
) -> list[_Record]:
    records: list[_Record] = []
    for path in paths:
        try:
            obj = read_json(path)
        except Exception:
            continue
        if not isinstance(obj, dict):
            if required_envelope:
                report.add(path, "Atom JSON must be an object")
            continue
        if required_envelope or ("id" in obj and "type" in obj):
            records.append(_Record(path=path, obj=obj))
    return records


def _validate_atom_envelope(report: ValidationReport, wp: WorldPaths, record: _Record) -> None:
    obj = record.obj
    for field_name in REQUIRED_ENVELOPE_FIELDS:
        if field_name not in obj:
            report.add(record.path, f"Missing required atom field '{field_name}'")

    if "id" in obj and not _is_nonempty_string(obj["id"]):
        report.add(record.path, "Atom field 'id' must be a non-empty string")
    if "type" in obj and not _is_nonempty_string(obj["type"]):
        report.add(record.path, "Atom field 'type' must be a non-empty string")
    if "name" in obj and not _is_nonempty_string(obj["name"]):
        report.add(record.path, "Atom field 'name' must be a non-empty string")
    if "summary" in obj and not isinstance(obj["summary"], str):
        report.add(record.path, "Atom field 'summary' must be a string")
    if "tags" in obj and not _is_string_list(obj["tags"]):
        report.add(record.path, "Atom field 'tags' must be a list of strings")
    if "refs" in obj and not isinstance(obj["refs"], dict):
        report.add(record.path, "Atom field 'refs' must be an object")
    if "data" in obj and not isinstance(obj["data"], dict):
        report.add(record.path, "Atom field 'data' must be an object")


def _validate_atom_path_convention(report: ValidationReport, wp: WorldPaths, record: _Record) -> None:
    atom_id = record.obj.get("id")
    atom_type = record.obj.get("type")
    if not isinstance(atom_id, str) or not isinstance(atom_type, str):
        return

    expected_prefix = f"{atom_type}."
    if not atom_id.startswith(expected_prefix):
        report.add(record.path, f"Atom id '{atom_id}' should start with '{expected_prefix}'")

    try:
        rel = record.path.relative_to(wp.atoms_dir)
    except ValueError:
        return
    if len(rel.parts) >= 2 and rel.parts[0] != atom_type:
        report.add(record.path, f"Atom type '{atom_type}' does not match atoms/{rel.parts[0]} folder")


def _validate_type_schema(report: ValidationReport, record: _Record) -> None:
    atom_type = record.obj.get("type")
    if not isinstance(atom_type, str):
        return

    schema = schema_for(atom_type)
    if schema is None:
        return

    for path, expected_type in schema.get("required", {}).items():
        exists, value = get_path(record.obj, path)
        if not exists:
            report.add(record.path, f"Type '{atom_type}' missing required field '{path}'")
            continue
        _validate_schema_value(report, record, atom_type, path, value, expected_type)

    for path, expected_type in schema.get("optional", {}).items():
        exists, value = get_path(record.obj, path)
        if exists:
            _validate_schema_value(report, record, atom_type, path, value, expected_type)


def _validate_schema_value(
    report: ValidationReport,
    record: _Record,
    atom_type: str,
    path: str,
    value: Any,
    expected_type: type,
) -> None:
    if not isinstance(value, expected_type):
        report.add(
            record.path,
            f"Type '{atom_type}' field '{path}' must be a {expected_type_name(expected_type)}",
        )
        return
    if expected_type is str and not value.strip():
        report.add(record.path, f"Type '{atom_type}' field '{path}' must not be empty")
    if path.endswith("canon_tier") and isinstance(value, str) and value not in CANON_TIERS:
        report.add(
            record.path,
            f"Type '{atom_type}' field '{path}' must be one of: {', '.join(sorted(CANON_TIERS))}",
        )


def _validate_references(
    report: ValidationReport,
    wp: WorldPaths,
    record: _Record,
    *,
    known_ids: set[str],
) -> None:
    for ref in _iter_references(record.obj):
        if ref.startswith("doc.") and ref not in known_ids:
            report.add(record.path, f"Broken reference '{ref}'")
        elif "." in ref and ref not in known_ids and not _looks_like_file_path(ref):
            report.add(record.path, f"Broken reference '{ref}'")


def _iter_references(obj: dict[str, Any]) -> Iterable[str]:
    refs = obj.get("refs")
    if isinstance(refs, dict):
        yield from _string_values(refs)

    data = obj.get("data")
    if isinstance(data, dict):
        relationships = data.get("relationships")
        if isinstance(relationships, list):
            for rel in relationships:
                if isinstance(rel, dict):
                    yield from _string_values(rel.get("object"))
                    yield from _string_values(rel.get("subject"))
                else:
                    yield from _string_values(rel)


def _string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        if value.strip():
            yield value.strip()
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _looks_like_file_path(value: str) -> bool:
    return "/" in value or "\\" in value
