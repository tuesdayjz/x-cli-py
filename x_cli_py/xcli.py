import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from x_cli_py.theme import log


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
