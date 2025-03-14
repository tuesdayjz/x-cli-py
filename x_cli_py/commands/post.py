import os
from typing import Optional

import typer
from rich.panel import Panel
from x_cli_py.theme import log, console
from x_cli_py.xcli import XComCLI
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def post_command(user_data_dir: Optional[str] = None):
    """Post a new tweet with your editor"""

    cli = XComCLI(user_data_dir=user_data_dir)

    if not cli.user_data_dir or not os.path.exists(cli.user_data_dir):
        console.print(
            "[error]Setup has not been completed. Please run the setup command first.[/error]"
        )
        raise typer.Exit(code=1)

    cli.initialize_driver()

    try:
        log.info("Navigating to X.com home page...")
        cli.driver.get("https://x.com/home")

        log.info("Looking for post input field...")
        post_input = WebDriverWait(cli.driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[@data-testid='tweetTextarea_0']",
            ))
        )
        post_input.click()
        content = typer.edit(
            "# Enter your post content here\n# lines starting with '#' will be ignored\n"
        )
        if not content:
            console.print("[warning]No content provided. Aborting post.[/warning]")
            raise cli.driver.quit()
        content = "\n".join([
            line for line in content.split("\n") if not line.startswith("#")
        ])
        if not content:
            console.print("[warning]No content provided. Aborting post.[/warning]")
            raise cli.driver.quit()
        post_content = []
        for line in content.split("\n"):
            post_content.append(line.split("#")[0].strip())
        content = "\n".join(post_content)
        post_input.send_keys(content)

        console.print(
            Panel.fit(
                content,
                title="Post Content",
                border_style="cyan",
            )
        )

        log.info("Submitting post...")
        post_button = WebDriverWait(cli.driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[@data-testid='tweetButtonInline']",
            ))
        )
        post_button.click()

        console.print("[success]Successfully posted![/success]")

    except Exception as e:
        log.error(f"Error posting: {e}")
        raise typer.Exit(code=1)

    finally:
        cli.driver.quit()
