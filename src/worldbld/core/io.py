from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: Path, obj: Any, pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        if pretty:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        else:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def print_json(obj: Any, pretty: bool, jsonl: bool = False) -> None:
    if jsonl:
        # expecting list of objects
        if isinstance(obj, list):
            for item in obj:
                print(json.dumps(item, ensure_ascii=False))
        else:
            print(json.dumps(obj, ensure_ascii=False))
        return

    if pretty:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
