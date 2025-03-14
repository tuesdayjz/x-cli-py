import os
from typing import Optional

import typer
from rich.panel import Panel
from x_cli_py.theme import log, console
from x_cli_py.xcli import XComCLI
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def whoami_command(user_data_dir: Optional[str] = None):
    """Display information about the currently logged in user"""

    cli = XComCLI(user_data_dir=user_data_dir)

    if not cli.user_data_dir or not os.path.exists(cli.user_data_dir):
        console.print(
            "[error]Setup has not been completed. Please run the setup command first.[/error]"
        )
        raise typer.Exit(code=1)

    cli.initialize_driver()

    try:
        log.info("Navigating to profile page...")
        cli.driver.get("https://x.com/home")

        try:
            profile_link = WebDriverWait(cli.driver, 3).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//a[@data-testid='AppTabBar_Profile_Link']",
                ))
            )
            profile_link.click()

            user_name = WebDriverWait(cli.driver, 3).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[@data-testid='UserName']",
                ))
            )
            user_name_text = user_name.text.split("\n")[0]
            user_id_text = user_name.text.split("\n")[1]

            try:
                bio = cli.driver.find_element(
                    By.XPATH, "//div[@data-testid='UserDescription']"
                )
                bio_text = bio.text
            except Exception:
                bio_text = "[No bio]"

            try:
                stats = cli.driver.find_elements(
                    By.XPATH,
                    f"//a[@href='/{user_id_text.strip('@')}/following']/span/span",
                )
                following = stats[0].text
                stats = cli.driver.find_elements(
                    By.XPATH,
                    f"//a[@href='/{user_id_text.strip('@')}/verified_followers']/span/span",
                )
                followers = stats[0].text
            except Exception:
                following = "Unknown"
                followers = "Unknown"

            profile_panel = Panel(
                f"[bold]{user_name_text}[/bold] / {user_id_text}\n\n"
                f"[bold]Bio:[/bold] {bio_text}\n\n"
                f"[bold]Following:[/bold] {following}, [bold]Followers:[/bold] {followers}",
                title="User Profile Information",
                border_style="cyan",
            )
            console.print(profile_panel)

        except Exception as e:
            log.error(f"Could not retrieve profile information: {e}")

    except Exception as e:
        log.error(f"Error: {e}")
        raise typer.Exit(code=1)

    finally:
        cli.driver.quit()
