import json
import os
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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


app = typer.Typer(
    help="X.com CLI Tool - Interact with X.com from your terminal",
    callback=set_log_level,
)


class XComCLI:
    CONFIG_FILE = "xcom_config.json"

    def __init__(self, user_data_dir=None):
        self.user_data_dir = user_data_dir
        self.driver = None

        if not self.user_data_dir:
            self.load_config()

    def load_config(self):
        """Load user data directory from config file"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    config = json.load(f)

                if "user_data_dir" in config and os.path.exists(
                    config["user_data_dir"]
                ):
                    self.user_data_dir = config["user_data_dir"]
                    log.info(f"Loaded user data directory: {self.user_data_dir}")
            except Exception as e:
                log.error(f"Failed to load config file: {e}")

    def save_config(self):
        """Save user data directory to config file"""
        config = {"user_data_dir": self.user_data_dir}

        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(config, f)
            log.info(f"Configuration saved to {self.CONFIG_FILE}")
        except Exception as e:
            log.error(f"Failed to save config: {e}")

    def initialize_driver(self, headless=True):
        """Initialize Selenium WebDriver with options"""
        options = Options()
        if headless:
            options.add_argument("--headless")
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        self.driver = webdriver.Chrome(options=options)


@app.command()
def setup(user_data_dir: Optional[str] = None):
    """Set up X.com authentication and save session"""

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


@app.command()
def post(user_data_dir: Optional[str] = None):
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
        post_input = WebDriverWait(cli.driver, 3).until(
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
        post_button = WebDriverWait(cli.driver, 3).until(
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


@app.command(name="tl")
def timeline(
    user_data_dir: Optional[str] = None,
    tab: int = 2,
):
    """Get the latest posts from the timeline"""

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

        try:
            log.info(f"Selecting tab {tab}...")
            tablist = WebDriverWait(cli.driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[@role='tablist']",
                ))
            )

            tabs = tablist.find_elements(By.XPATH, "./div[@role='presentation']")

            if len(tabs) >= tab:
                try:
                    tab_name = tabs[tab - 1].text
                except Exception:
                    tab_name = f"Tab {tab}"

                console.print(f"Selected tab: [info]{tab_name}[/info]")
                tabs[tab - 1].click()
            else:
                console.print(
                    f"[warning]Tab index {tab} is out of range. There are only {len(tabs)} tabs.[/warning]"
                )
                console.print("Continuing with the current view.")
        except Exception as e:
            log.warning(f"Could not select tab: {e}")
            console.print("[warning]Continuing with current view.[/warning]")

        posts_data = []

        log.info("Fetching posts...")
        post_articles = WebDriverWait(cli.driver, 2).until(
            EC.presence_of_all_elements_located((
                By.XPATH,
                "//article[@data-testid='tweet']",
            ))
        )

        count = 0
        for article in post_articles:
            post_data = {}

            try:
                user_info = article.find_element(
                    By.XPATH, ".//div[@data-testid='User-Name']"
                )
                post_data["user_info"] = " / ".join(user_info.text.split("\n")[:2])
            except Exception:
                post_data["user_info"] = "Unknown user"

            try:
                post_text = article.find_element(
                    By.XPATH, ".//div[@data-testid='tweetText']"
                )
                post_data["text"] = post_text.text
            except Exception:
                post_data["text"] = "[No text content]"

            try:
                timestamp = article.find_element(By.XPATH, ".//time")
                post_data["time"] = (
                    timestamp.get_attribute("datetime") or "Unknown time"
                )
            except Exception:
                post_data["time"] = "Unknown time"

            try:
                image_elements = article.find_elements(
                    By.XPATH, ".//div[@data-testid='tweetPhoto']//img"
                )
                post_data["images"] = f"{len(image_elements)} images"
            except Exception:
                post_data["images"] = "0 images"

            try:
                time_parent = timestamp.find_element(By.XPATH, "./ancestor::a")
                post_url = time_parent.get_attribute("href")
                if not post_url:
                    raise Exception("No URL found")
                post_data["url"] = post_url
            except Exception:
                post_data["url"] = "URL fetch failed"

            posts_data.append(post_data)
            count += 1

        console.print(
            Panel.fit(
                f"Latest {len(posts_data)} posts from timeline", border_style="cyan"
            )
        )

        for i, post in enumerate(posts_data, 1):
            text = Text()
            text.append(f"{i}. ", style="cyan")
            text.append(f"{post['user_info']}", style="user_info")
            text.append("\n   ")
            text.append(f"{'\n   '.join(post['text'].split('\n'))}")
            text.append("\n   ")
            if post["images"] != "0 images":
                text.append("\n   ")
                text.append(f"Images: {post['images']}", style="images")
            text.append("\n   ")
            text.append(f"URL: {post['url']}", style="info")
            text.append("\n   ")
            text.append(f"Time: {post['time']}", style="timestamp")

            console.print(text)
            console.rule(style="dim")

    except Exception as e:
        log.error(f"Error fetching timeline: {e}")
        raise typer.Exit(code=1)

    finally:
        cli.driver.quit()


@app.command()
def whoami(user_data_dir: Optional[str] = None):
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


if __name__ == "__main__":
    app()
