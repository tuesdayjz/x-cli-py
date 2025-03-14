import os
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table
from x_cli_py.theme import log, console
from x_cli_py.xcli import XComCLI
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def timeline_command(
    user_data_dir: Optional[str] = None, tab: int = 2, user: Optional[str] = None
):
    cli = XComCLI(user_data_dir=user_data_dir)

    if not cli.user_data_dir or not os.path.exists(cli.user_data_dir):
        console.print(
            "[error]Setup has not been completed. Please run the setup command first.[/error]"
        )
        raise typer.Exit(code=1)

    cli.initialize_driver()

    try:
        if user:
            log.info(f"Opening {user}'s profile page...")
            cli.driver.get(f"https://x.com/{user}")
        else:
            log.info("Navigating to X.com home page...")
            cli.driver.get("https://x.com/home")

        try:
            if not user:
                log.info(f"Selecting tab {tab}...")
                tablist = WebDriverWait(cli.driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[@role='tablist']",
                    ))
                )

                tabs = tablist.find_elements(By.XPATH, "./div[@role='presentation']")

                if len(tabs) >= tab - 1:
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
        post_articles = WebDriverWait(cli.driver, 10).until(
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

                display_name_element = user_info.find_element(By.XPATH, ".//span")
                username_element = user_info.find_element(
                    By.XPATH, ".//span[contains(text(), '@')]"
                )

                display_name = (
                    display_name_element.get_attribute("innerText")
                    or username_element.text
                )

                handle = username_element.text.strip()
                username = handle.replace("@", "")

                post_data["display_name"] = display_name
                post_data["username"] = username
                post_data["user_info"] = f"{display_name} / {handle}"
                post_data["profile_url"] = f"https://x.com/{username}"
            except Exception as e:
                log.warning(f"Error extracting user info: {e}")
                post_data["display_name"] = "Unknown user"
                post_data["username"] = "unknown"
                post_data["user_info"] = "Unknown user"
                post_data["profile_url"] = "#"

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
                post_data["images"] = str(len(image_elements))
            except Exception:
                post_data["images"] = "0"

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

        table = Table(show_header=True, expand=True, show_lines=True)
        table.add_column("User", style="cyan")
        table.add_column("Content", style="white", ratio=3)
        table.add_column("Timestamp", style="dim", justify="right")

        for i, post in enumerate(posts_data, 1):
            profile_link = f"[link={post['profile_url']}]{post['display_name']}[/link]"
            profile = (
                f"[user_info]{profile_link}" + f" / @{post['username']}[/user_info]"
            )
            header = f"[cyan]{i}.[/cyan] " + profile

            text = f"{post['text']}"
            if post["images"] != "0":
                text += f" :camera:[bold green] x {post['images']} [/bold green]"

            timestamp_text = " ".join(post["time"].split(".")[0].split("T"))
            timestamp_text = (
                f"[link={post['url']}][timestamp]{timestamp_text}[/timestamp][/link]"
            )

            table.add_row(header, text, timestamp_text)

        console.print(table)

    except Exception as e:
        log.error(f"Error fetching timeline: {e}")
        raise typer.Exit(code=1)

    finally:
        cli.driver.quit()
