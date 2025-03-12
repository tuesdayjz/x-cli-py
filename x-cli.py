import argparse
import json
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class XComCLI:
    CONFIG_FILE = "xcom_config.json"

    def __init__(self, user_data_dir=None):
        self.user_data_dir = user_data_dir
        self.driver = None

        if not self.user_data_dir:
            self.load_config()

    def load_config(self):
        """load config from config file"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    config = json.load(f)

                if "user_data_dir" in config and os.path.exists(
                    config["user_data_dir"]
                ):
                    self.user_data_dir = config["user_data_dir"]
            except Exception as e:
                print(f"Failed to load config file: {e}")

    def save_config(self):
        """save info to config file"""
        config = {"user_data_dir": self.user_data_dir}

        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(config, f)
            print(f"Saved config to {self.CONFIG_FILE}")
        except Exception as e:
            print(f"Failed to save config: {e}")

    def initialize_driver(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        self.driver = webdriver.Chrome(options=options)

    def setup(self):
        if not self.user_data_dir:
            default_dir = os.path.join(os.getcwd(), "xcom_user_data")
            self.user_data_dir = (
                input(
                    f"Enter the path to the user data directory (default: {default_dir}): "
                )
                or default_dir
            )

            if not os.path.exists(self.user_data_dir):
                os.makedirs(self.user_data_dir)

        self.initialize_driver(headless=False)

        self.driver.get("https://x.com/")
        print("Please login to your account in the opened browser window.")

        input("Press Enter after logging in...")

        self.driver.get("https://x.com/home")

        current_url = self.driver.current_url
        if "home" in current_url:
            print("Setup was successful!")
            print(f"User data directory: {self.user_data_dir}")

            self.save_config()
        else:
            print("Setup failed, please try again.")

        self.driver.quit()

    def post(self):
        if not self.user_data_dir or not os.path.exists(self.user_data_dir):
            print("Setup has not been completed. Please run the setup command first.")
            return

        self.initialize_driver()

        try:
            self.driver.get("https://x.com/home")

            post_input = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[@data-testid='postTextarea_0']",
                ))
            )

            post_content = input("Enter your post: ")
            post_input.send_keys(post_content)

            post_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[@data-testid='postButtonInline']",
                ))
            )
            post_button.click()

            print("Posted!")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            self.driver.quit()

    def get_timeline(self, tab_index=2):
        """Get the latest 10 posts from the specified tab

        Args:
            tab_index (int): The tab index to select (1-based, default is 2 for 'Following')
        """
        if not self.user_data_dir or not os.path.exists(self.user_data_dir):
            print("Setup has not been completed. Please run the setup command first.")
            return

        self.initialize_driver()

        try:
            self.driver.get("https://x.com/home")
            try:
                tablist = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[@role='tablist']",
                    ))
                )

                tabs = tablist.find_elements(By.XPATH, "./div[@role='presentation']")

                if len(tabs) >= tab_index:
                    try:
                        tab_name = tabs[tab_index - 1].text
                    except Exception:
                        tab_name = f"Tab {tab_index}"

                    print(f"Tab: {tab_name}")

                    tabs[tab_index - 1].click()
                else:
                    print(
                        f"Tab index {tab_index} is out of range. There are only {len(tabs)} tabs."
                    )
                    print("Continuing with the current view.")
            except Exception as e:
                print(f"Could not select tab: {e}")
                print("Continuing with current view.")

            posts_data = []
            post_articles = WebDriverWait(self.driver, 2).until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    "//article[@data-testid='tweet']",
                ))
            )

            count = 0
            for article in post_articles:
                if count >= 10:
                    break

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
                    post_data["time"] = timestamp.get_attribute("datetime")
                except Exception:
                    post_data["time"] = "Unknown time"

                posts_data.append(post_data)
                count += 1

            print(f"\n{'=' * 50}")
            print(f"Latest {len(posts_data)} posts from timeline:")
            print(f"{'=' * 50}\n")

            for i, post in enumerate(posts_data, 1):
                print(f"{i}. {post['user_info']}")
                print(f"   {post['text']}")
                print(f"   Time: {post['time']}")
                print(f"   {'-' * 40}")

        except Exception as e:
            print(f"Error fetching timeline: {e}")

        finally:
            self.driver.quit()

    def whoami(self):
        """Display information about the currently logged in user"""
        if not self.user_data_dir or not os.path.exists(self.user_data_dir):
            print("Setup has not been completed. Please run the setup command first.")
            return

        self.initialize_driver()

        try:
            self.driver.get("https://x.com/home")

            try:
                profile_link = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//a[@data-testid='AppTabBar_Profile_Link']",
                    ))
                )
                profile_link.click()

                user_name = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[@data-testid='UserName']",
                    ))
                )
                user_name = " / ".join(user_name.text.split("\n")[:2])

                try:
                    bio = self.driver.find_element(By.XPATH, "//div[@data-testid='UserDescription']")
                    bio_text = bio.text
                except Exception:
                    bio_text = "[No bio]"

                print("\n" + "="*50)
                print("User Profile Information:")
                print("="*50)
                print(f"Name: {user_name}")
                print(f"Bio: {bio_text}")

            except Exception as e:
                print(f"Could not retrieve profile information: {e}")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            self.driver.quit()



def main():
    parser = argparse.ArgumentParser(description="X.com CLI Tool")
    parser.add_argument(
        "command", choices=["setup", "post", "tl", "whoami"], help="command to run"
    )
    parser.add_argument("--user-data-dir", help="Path to user data directory")
    parser.add_argument(
        "--tab",
        type=int,
        default=2,
        help="Tab index to select (1-based, default: 2 for 'Following')",
    )

    args = parser.parse_args()

    cli = XComCLI(user_data_dir=args.user_data_dir)

    if args.command == "setup":
        cli.setup()
    elif args.command == "post":
        cli.post()
    elif args.command == "tl":
        cli.get_timeline(tab_index=args.tab)
    elif args.command == "whoami":
        cli.whoami()


if __name__ == "__main__":
    main()
