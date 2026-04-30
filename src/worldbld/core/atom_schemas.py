from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_VERSION = "worldcodex.atom_schemas.v1"

CANON_TIERS = {"core_canon", "established", "rumored", "deprecated"}

TYPE_SCHEMAS: dict[str, dict[str, Any]] = {
    "place": {
        "required": {
            "data.logline": str,
        },
        "optional": {
            "data.relationships": list,
            "data.prompt_hooks": list,
            "data.tone": dict,
        },
    },
    "character": {
        "required": {
            "data.role_in_world": dict,
            "data.voice": dict,
            "data.relationships": list,
            "data.story_hooks": list,
        },
        "optional": {
            "data.pressures": list,
            "data.secrets_and_fears": dict,
            "data.prompt_knobs": dict,
        },
    },
    "org": {
        "required": {
            "data.prompt_hooks": list,
            "data.tone": dict,
        },
        "optional": {
            "data.relationships": list,
            "data.values_and_blind_spots": dict,
        },
    },
    "faction": {
        "required": {
            "data.ideology": str,
            "data.resources": list,
            "data.territory": list,
            "data.allies": list,
            "data.enemies": list,
            "data.public_goals": list,
            "data.private_goals": list,
            "data.current_pressure": str,
        },
        "optional": {
            "data.relationships": list,
            "data.tone": dict,
        },
    },
    "culture": {
        "required": {
            "data.prompt_hooks": list,
            "data.tone": dict,
        },
        "optional": {
            "data.relationships": list,
            "data.origin": dict,
            "data.ritual": dict,
        },
    },
    "tech": {
        "required": {
            "data.role": str,
            "data.components": list,
        },
        "optional": {
            "data.relationships": list,
            "data.failure_modes": list,
            "data.prompt_hooks": list,
        },
    },
    "event": {
        "required": {
            "data.date_or_era": str,
            "data.participants": list,
            "data.locations": list,
            "data.causes": list,
            "data.consequences": list,
            "data.canon_tier": str,
        },
        "optional": {
            "data.relationships": list,
            "data.sources": list,
        },
    },
    "conflict": {
        "required": {
            "data.parties": list,
            "data.stakes": str,
            "data.current_state": str,
            "data.escalation_paths": list,
            "data.possible_resolutions": list,
        },
        "optional": {
            "data.relationships": list,
            "data.canon_tier": str,
        },
    },
    "artifact": {
        "required": {
            "data.origin": str,
            "data.current_location": str,
            "data.significance": str,
            "data.history": list,
            "data.story_hooks": list,
        },
        "optional": {
            "data.relationships": list,
            "data.visual_identity": dict,
            "data.canon_tier": str,
        },
    },
    "doc": {
        "required": {
            "data.doc_type": str,
            "data.status": dict,
            "data.prompt_hooks": list,
        },
        "optional": {
            "data.relationships": list,
            "data.date": str,
            "data.classification": str,
        },
    },
}


def schema_for(atom_type: str) -> dict[str, Any] | None:
    return TYPE_SCHEMAS.get(atom_type)


def atom_data_template(atom_type: str) -> dict[str, Any]:
    template = DATA_TEMPLATES.get(atom_type, {})
    return deepcopy(template)


def get_path(obj: dict[str, Any], dotted_path: str) -> tuple[bool, Any]:
    cur: Any = obj
    for part in dotted_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, cur


def expected_type_name(expected_type: type) -> str:
    if expected_type is str:
        return "string"
    if expected_type is list:
        return "list"
    if expected_type is dict:
        return "object"
    return expected_type.__name__


DATA_TEMPLATES: dict[str, dict[str, Any]] = {
    "place": {
        "logline": "TBD",
        "environment": {
            "terrain": [],
            "climate": "",
            "sensory_details": [],
        },
        "hazards": [],
        "factions_present": [],
        "visual_identity": {
            "materials": [],
            "lighting": [],
            "motifs": [],
        },
        "relationships": [],
        "story_hooks": [],
        "tone": {
            "keywords": [],
            "avoid": [],
        },
    },
    "character": {
        "role_in_world": {
            "occupation": "",
            "affiliation": "",
            "status": "",
        },
        "relationships": [],
        "goals": [],
        "secrets": [],
        "voice": {
            "speech_style": "",
            "tells": [],
            "sample_lines": [],
        },
        "arc_hooks": [],
        "story_hooks": [],
    },
    "org": {
        "ideology": "TBD",
        "resources": [],
        "territory": [],
        "allies": [],
        "enemies": [],
        "public_goals": [],
        "private_goals": [],
        "current_pressure": "TBD",
        "relationships": [],
        "prompt_hooks": [],
        "tone": {
            "keywords": [],
            "avoid": [],
        },
    },
    "faction": {
        "ideology": "TBD",
        "resources": [],
        "territory": [],
        "allies": [],
        "enemies": [],
        "public_goals": [],
        "private_goals": [],
        "current_pressure": "TBD",
        "relationships": [],
        "tone": {
            "keywords": [],
            "avoid": [],
        },
    },
    "culture": {
        "origin": {
            "story": "",
            "first_observed": "",
        },
        "ritual": {
            "steps": [],
            "symbols": [],
        },
        "relationships": [],
        "prompt_hooks": [],
        "tone": {
            "keywords": [],
            "avoid": [],
        },
    },
    "tech": {
        "role": "TBD",
        "components": [],
        "relationships": [],
        "failure_modes": [],
        "prompt_hooks": [],
    },
    "event": {
        "date_or_era": "TBD",
        "participants": [],
        "locations": [],
        "causes": [],
        "consequences": [],
        "canon_tier": "established",
        "relationships": [],
        "sources": [],
    },
    "conflict": {
        "parties": [],
        "stakes": "TBD",
        "current_state": "TBD",
        "escalation_paths": [],
        "possible_resolutions": [],
        "canon_tier": "established",
        "relationships": [],
    },
    "artifact": {
        "origin": "TBD",
        "current_location": "TBD",
        "significance": "TBD",
        "history": [],
        "story_hooks": [],
        "canon_tier": "established",
        "relationships": [],
        "visual_identity": {
            "materials": [],
            "motifs": [],
        },
    },
    "doc": {
        "doc_type": "TBD",
        "status": {
            "official": "",
            "practical": "",
        },
        "prompt_hooks": [],
        "relationships": [],
        "date": "",
        "classification": "",
    },
}
