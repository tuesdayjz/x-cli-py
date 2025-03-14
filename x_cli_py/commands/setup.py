import os
from typing import Optional

import typer
from rich.panel import Panel
from x_cli_py.theme import log, console
from x_cli_py.xcli import XComCLI


def setup_command(user_data_dir: Optional[str] = None):
    cli = XComCLI(user_data_dir=user_data_dir)

    if not cli.user_data_dir:
        default_dir = os.path.join(os.getcwd(), "xcom_user_data")
        cli.user_data_dir = typer.prompt(
            "Enter the path to the user data directory", default=default_dir
        )

        if not os.path.exists(cli.user_data_dir):
            os.makedirs(cli.user_data_dir)
            log.info(f"Created directory: {cli.user_data_dir}")

    cli.initialize_driver(headless=False)

    try:
        log.info("Opening X.com login page...")
        cli.driver.get("https://x.com/")

        console.print(
            Panel.fit(
                "Please log in to your X.com account in the opened browser window.",
                title="Authentication Required",
                border_style="cyan",
            )
        )

        typer.prompt("Press Enter after logging in...", default="", show_default=False)

        cli.driver.get("https://x.com/home")
        log.info("Verifying login status...")

        current_url = cli.driver.current_url
        if "home" in current_url:
            console.print("[success]Setup was successful![/success]")
            console.print(f"User data directory: {cli.user_data_dir}")

            cli.save_config()
        else:
            console.print("[error]Setup failed, please try again.[/error]")
    finally:
        cli.driver.quit()
