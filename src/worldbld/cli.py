import typer

from worldbld.commands.init_cmd import init
from worldbld.commands.add_cmd import add
from worldbld.commands.get_cmd import get
from worldbld.commands.build_cmd import build
from worldbld.commands.export_cmd import export_context
from worldbld.commands.validate_cmd import validate
from worldbld.commands.query_cmd import app as query_app
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
app.command("validate")(validate)
app.command("export")(export_context)
app.add_typer(query_app, name="query")
app.add_typer(view_app, name="view")

if __name__ == "__main__":
    app()
