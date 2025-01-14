from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import logging
from computer_use_demo.loop import perform_action
from anthropic import AnthropicBedrock
from computer_use_demo.tools.computer import ComputerTool
from computer_use_demo.tools.toolbox import ToolBox
from computer_use_demo.executors.guacamole_executor import GuacamoleExecutor
from copy import deepcopy
from sys import argv

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

GUAC_URL = argv[1]
ACTION_DESCRIPTION = argv[2]
MODEL = os.environ.get("COMPUTER_USE_MODEL", "claude-3-5-sonnet-latest")

# XGA resolution (using halved values since screenshots double the resolution)
SCREEN_WIDTH = 1024 // 2
SCREEN_HEIGHT = 768 // 2
CHROME_HEADER = 139


def on_new_message_callback(message: dict):
    msg_copy = deepcopy(message)
    if isinstance(msg_copy.get("content"), list):
        for content_item in msg_copy["content"]:
            if "content" in content_item:
                for inner_content_item in content_item["content"]:
                    if "source" in inner_content_item:
                        inner_content_item["source"] = "TRUNCATED"

    LOGGER.info(f"Received message: {msg_copy}")


def main():
    chrome_options = Options()
    arg = f"--window-size={SCREEN_WIDTH},{SCREEN_HEIGHT + CHROME_HEADER}"
    chrome_options.add_argument(arg)
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    anthropic_client = AnthropicBedrock()

    try:
        # Navigate to the URL
        driver.get(GUAC_URL)

        # Wait for initial page load
        time.sleep(10)

        toolbox = ToolBox(
            ComputerTool(
                screen_width=SCREEN_WIDTH,
                screen_height=SCREEN_HEIGHT,
                executor=GuacamoleExecutor(driver),
            )
        )

        perform_action(
            anthropic_client=anthropic_client,
            model=MODEL,
            action_description=ACTION_DESCRIPTION,
            toolbox=toolbox,
            on_new_message_callback=on_new_message_callback,
        )

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
