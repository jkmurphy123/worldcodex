# WorldCodex Milestone Plan

Goal: evolve WorldCodex from a lightweight filesystem world pack into the canonical world-support layer for downstream tools such as fictional news generators, story generators, image prompt generators, and editing UIs.

The existing atom-based storage and view runner should remain the foundation. Each milestone below should leave the project runnable and testable before moving on.

## Milestone 1: Validation Baseline

Purpose: make the current flexible atom system safer without changing its core storage model.

Scope:
- Add a `world validate WORLD` CLI command.
- Validate required atom envelope fields: `id`, `type`, `name`, `summary`, `tags`, `refs`, `data`.
- Validate ID conventions such as `place.argonaut_station` matching atom type and filename where practical.
- Detect duplicate atom IDs.
- Detect invalid JSON files under `atoms/`, `views/`, and `docs/` when they are JSON.
- Detect broken local references in known reference containers, starting with `refs` and `data.relationships`.
- Return non-zero exit code on validation failure.

Acceptance tests:
- `world validate titan-osa` passes on the current sample world after any needed data cleanup.
- A duplicate atom ID causes validation to fail with a clear message.
- A relationship to a missing atom causes validation to fail with a clear message.
- Existing commands still work: `world init`, `world add`, `world build`, `world get`, and `world view run`.

Why this first:
Downstream tools cannot safely consume WorldCodex until the pack can prove that its IDs, JSON, and references are coherent.

## Milestone 2: Typed Atom Schemas

Purpose: keep the atom envelope flexible while adding reliable contracts for common worldbuilding entities.

Scope:
- Introduce versioned schema definitions for key atom types:
  - `place`
  - `character`
  - `org` or `faction`
  - `culture`
  - `tech`
  - `event`
  - `conflict`
  - `artifact`
  - `doc`
- Keep the common atom envelope unchanged.
- Define type-specific required and optional fields inside `data`.
- Add schema validation to `world validate`.
- Add `world add` templates for the main atom types so newly created atoms start with useful fields.
- Document each atom type in a developer-facing schema guide.

Suggested fields:
- Character: role, status, affiliations, relationships, goals, secrets, voice, location, arc_hooks.
- Place: parent_location, environment, sensory_details, hazards, factions_present, visual_identity, story_hooks.
- Faction/org: ideology, resources, territory, allies, enemies, public_goals, private_goals, current_pressure.
- Event: date or era, participants, locations, causes, consequences, canon_tier.
- Conflict: parties, stakes, current_state, escalation_paths, possible_resolutions.

Acceptance tests:
- Valid sample atoms pass schema validation.
- Missing required fields for a typed atom fail validation.
- `world add titan-osa character "New Person"` creates a schema-shaped character stub.
- Existing sample atoms either pass directly or have a documented compatibility path.

Why this second:
Story, news, and image generators need predictable fields. A generic `data` object is not enough once other apps depend on it.

## Milestone 3: Relationships, Timeline, and Canon State

Purpose: make WorldCodex understand the world as a graph and a continuity record, not just a folder of records.

Scope:
- Add first-class relationship records or a normalized relationship block.
- Support relationship fields:
  - subject
  - predicate
  - object
  - summary
  - canon_tier
  - source
  - start_date or era
  - end_date or status
- Add canon tiers:
  - `core_canon`
  - `established`
  - `rumored`
  - `deprecated`
- Add timeline/event support that can answer ordered history questions.
- Extend `world build` to emit graph and timeline indexes.
- Extend `world get` or add `world query` for common graph lookups:
  - entities related to an atom
  - factions active in a place
  - characters tied to a faction
  - unresolved conflicts
  - events involving an entity

Acceptance tests:
- `world build titan-osa` writes an index containing atoms, relationships, and timeline entries.
- A broken relationship fails `world validate`.
- A deprecated atom can remain in the world but is marked clearly in query results.
- A query can return all relationships for `place.argonaut_station`.

Why this third:
Rich generation depends on context: who knows whom, what caused what, which conflicts are open, and what is fixed canon versus rumor.

## Milestone 4: Stable Context Views for Downstream Apps

Purpose: turn the current view runner into a formal integration layer for other tools.

Scope:
- Define versioned built-in context exports:
  - `world_bible`
  - `story_context`
  - `news_context`
  - `image_context`
  - `character_context`
  - `location_context`
- Add a CLI path such as:
  - `world export titan-osa story-context --out ...`
  - `world export titan-osa news-context --out ...`
  - `world export titan-osa image-context --out ...`
- Keep custom JSON view files available for advanced use.
- Make each export schema explicit and documented.
- Include enough metadata for downstream tools:
  - schema version
  - world ID
  - generated timestamp
  - source atom IDs
  - canon tier filtering
- Add filtering options:
  - by location
  - by character
  - by faction
  - by tags
  - by canon tier

Acceptance tests:
- `world export titan-osa news-context` produces valid JSON with factions, places, conflicts, timeline, and open threads.
- `world export titan-osa image-context --location place.argonaut_station` produces visual identity, materials, motifs, constraints, and relevant location details.
- `world export titan-osa story-context --character character.elara_myung` produces character, relationships, locations, active conflicts, and tone constraints.
- Export schemas are stable enough for `world_weaver` to consume in a later integration.

Why this fourth:
WorldCodex should not become every generator. It should provide high-quality world context that other apps can call reliably.

## Milestone 5: Patch Workflow and External App Integration

Purpose: let downstream apps propose changes to canon while WorldCodex remains the source of truth.

Scope:
- Add a patch format for proposed world changes:
  - add atom
  - update atom
  - deprecate atom
  - add relationship
  - update relationship
  - add timeline event
  - resolve conflict or open thread
- Add CLI commands:
  - `world patch validate PATCH`
  - `world patch preview WORLD PATCH`
  - `world patch apply WORLD PATCH`
- Archive applied patches under the world folder.
- Require validation before patch application.
- Add an integration contract for external tools:
  - context request shape
  - generated output shape
  - proposed patch shape
- Create an example integration flow with `world_weaver`:
  - WorldCodex exports `news_context`.
  - World Weaver generates a story batch.
  - World Weaver writes a proposed canon patch.
  - WorldCodex validates/previews/applies the patch.

Acceptance tests:
- A valid patch adds a new event and relationship, then `world validate` still passes.
- An invalid patch referencing a missing atom fails before application.
- Patch preview clearly shows changed atoms, relationships, and timeline entries.
- A sample `world_weaver`-style patch can be applied to the sample world.

Why this fifth:
Once other tools generate from a world, they need a controlled way to feed lasting changes back into canon without corrupting the source world pack.

## Final Target Architecture

WorldCodex should own:
- canonical world packs
- typed entities
- relationships
- timeline/history
- canon state
- validation
- context exports
- patch intake

Downstream tools should own:
- news generation
- story generation
- image prompt generation
- UI workflows
- model/provider-specific behavior

In this architecture, WorldCodex is the stable world support layer. Other apps call it for context and submit patches back to it when they want to change canon.
