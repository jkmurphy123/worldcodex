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

## Schemas
Known atom types use schema-shaped `data` templates and validation. See
`ATOM_SCHEMA_GUIDE.md` for the current typed atom contracts.
