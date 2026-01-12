# worldbld

A filesystem-based worldbuilding pack + Typer CLI.

## Dev install
pip install -e .

## Try it
world init titan-osa --title "Argonaut Station (Titan)"
world add titan-osa place "Argonaut Station"
world build titan-osa
world get titan-osa --type place --pretty
