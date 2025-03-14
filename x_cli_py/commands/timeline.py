import os
from typing import Optional

import typer
from rich.panel import Panel
from rich.text import Text
from x_cli_py.theme import log, console
from x_cli_py.xcli import XComCLI
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def timeline_command(
    user_data_dir: Optional[str] = None,
    tab: int = 2,
):
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
            text.append(f"Post URL: {post['url']}", style="info")
            text.append("\n   ")
            text.append(f"Time: {post['time']}", style="timestamp")

            console.print(text)
            console.rule(style="dim")

    except Exception as e:
        log.error(f"Error fetching timeline: {e}")
        raise typer.Exit(code=1)

    finally:
        cli.driver.quit()
