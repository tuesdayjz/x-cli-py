import logging
import typer

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "timestamp": "dim",
    "user_info": "bold blue",
})

console = Console(theme=custom_theme)

logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)],
)

log = logging.getLogger("xcom_cli")


def set_log_level(
    log_level: str = typer.Option(
        "error", help="Log level (debug, info, warning, error, critical)"
    ),
):
    """Set the logging level"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
        force=True,
    )

    log.setLevel(numeric_level)
    log.info(f"Log level set to {log_level.upper()}")
