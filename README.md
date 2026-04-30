# worldbld

A filesystem-based worldbuilding pack + Typer CLI.

## Dev install
pip install -e .

## Try it
world init titan-osa --title "Argonaut Station (Titan)"
world add titan-osa place "Argonaut Station"
world validate titan-osa
world build titan-osa
world get titan-osa --type place --pretty
world query relationships titan-osa place.argonaut_station
world export titan-osa news-context --out /tmp/news_context.json
world patch preview titan-osa /tmp/world_patch.json

## Schemas
Known atom types use schema-shaped `data` templates and validation. See
`ATOM_SCHEMA_GUIDE.md` for the current typed atom contracts.

## Context Exports
WorldCodex provides stable context exports for downstream tools:

```bash
world export titan-osa world-bible
world export titan-osa story-context --character character.elara_myung
world export titan-osa news-context
world export titan-osa image-context --location place.argonaut_station
world export titan-osa character-context --character character.elara_myung
world export titan-osa location-context --location place.argonaut_station
```

Use `--out PATH` to write the JSON to a file.

## Patches
Downstream tools can propose canon changes with versioned patch files:

```bash
world patch validate titan-osa /tmp/world_patch.json
world patch preview titan-osa /tmp/world_patch.json
world patch apply titan-osa /tmp/world_patch.json
```

Applied patches are archived under `patches/applied/` inside the world folder.
