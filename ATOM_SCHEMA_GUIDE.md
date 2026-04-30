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

## Adding Atoms

`world add` now creates schema-shaped templates for known atom types:

```bash
world add titan-osa character "New Person"
world add titan-osa event "First Contact"
world add titan-osa conflict "Dock Strike"
```

The generated atom is intentionally a valid starter object. Replace `TBD` and empty lists as the world becomes richer.
