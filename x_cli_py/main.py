import typer
from x_cli_py.theme import set_log_level
from x_cli_py.commands.setup import setup_command
from x_cli_py.commands.timeline import timeline_command
from x_cli_py.commands.post import post_command
from x_cli_py.commands.whoami import whoami_command

app = typer.Typer(
    help="X.com CLI Tool - Interact with X.com from your terminal",
    callback=set_log_level,
)


@app.command()
def setup(user_data_dir: str = typer.Option(None, help="User data directory")):
    """Set up X.com authentication and save session"""
    setup_command(user_data_dir=user_data_dir)


@app.command()
def tl(
    user_data_dir: str = typer.Option(None, help="User data directory"),
    tab: int = 2,
    user: str = typer.Option(None, help="Get specific user's timeline"),
):
    """Get the latest posts from the timeline"""
    timeline_command(user_data_dir=user_data_dir, tab=tab, user=user)


@app.command()
def post(user_data_dir: str = typer.Option(None, help="User data directory")):
    """Post a new tweet with your editor"""
    post_command(user_data_dir=user_data_dir)


@app.command()
def whoami(user_data_dir: str = typer.Option(None, help="User data directory")):
    """Get the current user information"""
    whoami_command(user_data_dir=user_data_dir)


if __name__ == "__main__":
    app()
