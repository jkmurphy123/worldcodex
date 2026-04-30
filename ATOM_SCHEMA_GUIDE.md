# Atom Schema Guide

WorldCodex stores world data as atom JSON files. Every atom keeps the same envelope, while common atom types add a typed `data` contract.

This guide documents the Milestone 2 schema baseline. The implementation lives in `src/worldbld/core/atom_schemas.py`.

## Common Envelope

All atom files under `atoms/` must be JSON objects with:

- `id`: stable ID such as `place.argonaut_station`
- `type`: atom type such as `place`
- `name`: human-facing name
- `summary`: short summary string
- `tags`: list of strings
- `refs`: object for references and metadata
- `data`: object containing type-specific fields

ID convention:

- The ID should start with the atom type plus a dot.
- A `place` atom should have an ID like `place.example`.
- The first folder under `atoms/` should match the atom type.

## Supported Typed Atoms

### `place`

Required:

- `data.logline`: string

Recommended:

- `data.environment`
- `data.hazards`
- `data.factions_present`
- `data.visual_identity`
- `data.relationships`
- `data.story_hooks`
- `data.tone`

### `character`

Required:

- `data.role_in_world`: object
- `data.voice`: object
- `data.relationships`: list
- `data.story_hooks`: list

Recommended:

- `data.goals`
- `data.secrets`
- `data.pressures`
- `data.secrets_and_fears`
- `data.prompt_knobs`
- `data.arc_hooks`

### `org`

Required:

- `data.prompt_hooks`: list
- `data.tone`: object

Recommended:

- `data.ideology`
- `data.resources`
- `data.territory`
- `data.allies`
- `data.enemies`
- `data.public_goals`
- `data.private_goals`
- `data.current_pressure`
- `data.relationships`

### `faction`

Required:

- `data.ideology`: string
- `data.resources`: list
- `data.territory`: list
- `data.allies`: list
- `data.enemies`: list
- `data.public_goals`: list
- `data.private_goals`: list
- `data.current_pressure`: string

Recommended:

- `data.relationships`
- `data.tone`

### `culture`

Required:

- `data.prompt_hooks`: list
- `data.tone`: object

Recommended:

- `data.origin`
- `data.ritual`
- `data.relationships`

### `tech`

Required:

- `data.role`: string
- `data.components`: list

Recommended:

- `data.relationships`
- `data.failure_modes`
- `data.prompt_hooks`

### `event`

Required:

- `data.date_or_era`: string
- `data.participants`: list
- `data.locations`: list
- `data.causes`: list
- `data.consequences`: list
- `data.canon_tier`: string

Recommended:

- `data.relationships`
- `data.sources`

### `conflict`

Required:

- `data.parties`: list
- `data.stakes`: string
- `data.current_state`: string
- `data.escalation_paths`: list
- `data.possible_resolutions`: list

Recommended:

- `data.relationships`
- `data.canon_tier`

### `artifact`

Required:

- `data.origin`: string
- `data.current_location`: string
- `data.significance`: string
- `data.history`: list
- `data.story_hooks`: list

Recommended:

- `data.relationships`
- `data.visual_identity`
- `data.canon_tier`

### `doc`

Required:

- `data.doc_type`: string
- `data.status`: object
- `data.prompt_hooks`: list

Recommended:

- `data.relationships`
- `data.date`
- `data.classification`

## Canon Tiers

Fields named `canon_tier` must use one of:

- `core_canon`
- `established`
- `rumored`
- `deprecated`

## Relationships

Atoms can define first-class relationships in `data.relationships`:

```json
{
  "predicate": "governed_by",
  "object": "org.outer_system_authority",
  "summary": "Optional human-readable note.",
  "canon_tier": "established",
  "source": "place.argonaut_station",
  "start_date": "2191-03-14",
  "end_date": null,
  "status": "active"
}
```

Required relationship fields:

- `predicate`: non-empty string
- `object`: referenced atom ID

Optional fields:

- `subject`: referenced atom ID; defaults to the containing atom ID
- `summary`
- `canon_tier`
- `source`
- `start_date`
- `end_date`
- `status`

`world build` emits normalized relationship records in `builds/index.json`:

- `relationships`: flat relationship list
- `relationship_map`: relationships keyed by subject and object IDs

## Timeline

`event` atoms form the timeline. Required event fields are:

- `data.date_or_era`
- `data.participants`
- `data.locations`
- `data.causes`
- `data.consequences`
- `data.canon_tier`

`world build` emits ordered event summaries in `builds/index.json` under `timeline`.

## Validation

Run:

```bash
world validate titan-osa
```

Validation checks:

- JSON parse errors in `atoms/`, `views/`, and `docs/`
- common atom envelope fields
- typed `data` schema fields
- duplicate IDs
- ID/type/path conventions
- broken references in `refs` and `data.relationships`
- broken references in event participants/locations and conflict parties
- malformed relationships

## Graph Queries

Milestone 3 adds graph and timeline query commands:

```bash
world query relationships titan-osa place.argonaut_station
world query factions-in titan-osa place.argonaut_station
world query characters-for titan-osa org.outer_system_authority
world query unresolved-conflicts titan-osa
world query events-for titan-osa place.argonaut_station
```

## Context Exports

Milestone 4 adds built-in context exports for downstream apps:

```bash
world export titan-osa world-bible
world export titan-osa story-context --character character.elara_myung
world export titan-osa news-context
world export titan-osa image-context --location place.argonaut_station
world export titan-osa character-context --character character.elara_myung
world export titan-osa location-context --location place.argonaut_station
```

Export metadata includes:

- `schema_version`
- `export_type`
- `world_id`
- `world_title`
- `generated_at`
- `source_atom_ids`
- `filters`

Supported filters:

- `--location`
- `--character`
- `--faction`
- `--tag`
- `--canon-tier`

Use `--out PATH` to write the export JSON to disk.

## Patch Workflow

Milestone 5 adds patch files for controlled canon updates from external tools.

Commands:

```bash
world patch validate titan-osa /tmp/world_patch.json
world patch preview titan-osa /tmp/world_patch.json
world patch apply titan-osa /tmp/world_patch.json
```

Patch format:

```json
{
  "schema_version": "worldcodex.patch.v1",
  "id": "example-news-patch",
  "description": "Canon changes proposed by a downstream generator.",
  "operations": [
    {
      "op": "add_timeline_event",
      "atom": {
        "id": "event.example",
        "type": "event",
        "name": "Example Event",
        "summary": "A short event summary.",
        "tags": [],
        "refs": {},
        "data": {
          "date_or_era": "2200-01-01",
          "participants": ["character.example"],
          "locations": ["place.example"],
          "causes": ["A cause."],
          "consequences": ["A consequence."],
          "canon_tier": "established",
          "relationships": [],
          "sources": []
        }
      }
    },
    {
      "op": "add_relationship",
      "subject": "character.example",
      "predicate": "witnessed",
      "object": "event.example",
      "summary": "Character witnessed the event."
    }
  ]
}
```

Supported operations:

- `add_atom`
- `update_atom`
- `deprecate_atom`
- `add_relationship`
- `update_relationship`
- `add_timeline_event`
- `resolve_conflict`

Patch validation checks:

- patch schema version
- supported operation names
- existing or newly added referenced atom IDs
- relationship subject/object references
- event participant/location references
- canon tier values

`world patch apply` validates first, applies operations, runs full `world validate`, rebuilds the index during operation processing, and archives the applied patch under `patches/applied/`.

## Adding Atoms

`world add` now creates schema-shaped templates for known atom types:

```bash
world add titan-osa character "New Person"
world add titan-osa event "First Contact"
world add titan-osa conflict "Dock Strike"
```

The generated atom is intentionally a valid starter object. Replace `TBD` and empty lists as the world becomes richer.
