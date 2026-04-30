import typer

from worldbld.commands.init_cmd import init
from worldbld.commands.add_cmd import add
from worldbld.commands.get_cmd import get
from worldbld.commands.build_cmd import build
from worldbld.commands.view_cmd import view_app

app = typer.Typer(
    name="world",
    help="WorldPack CLI: maintain worldbuilding data and export slices for other tools.",
    no_args_is_help=True,
)

app.command("init")(init)
app.command("add")(add)
app.command("get")(get)
app.command("build")(build)
app.add_typer(view_app, name="view")

if __name__ == "__main__":
    app()
