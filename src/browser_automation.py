from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time


class GuacamoleAutomation:
    def __init__(self, driver):
        self.driver = driver
        # Initialize the client once
        init_js = """
        var injector = angular.element(document.body).injector();
        var guacClientManager = injector.get('guacClientManager');
        var clients = guacClientManager.getManagedClients();
        var main = Object.values(clients)[0];
        main.managedDisplay.display.showCursor(true);
        window.guacClient = main.client;
        """
        self.driver.execute_script(init_js)

    def send_key(self, key_code, pressed):
        """
        Send a keyboard event to Guacamole

        Args:
            key_code (int): The key code to send (e.g., 97 for 'a')
            pressed (bool): True for key press, False for key release
        """
        js_code = f"window.guacClient.sendKeyEvent({int(pressed)}, {key_code});"
        self.driver.execute_script(js_code)

    def type_key(self, key_code):
        """
        Simulate a complete keypress (press and release) for a key

        Args:
            key_code (int): The key code to send
        """
        self.send_key(key_code, True)  # Press
        self.send_key(key_code, False)  # Release

    def type_string(self, text):
        """
        Type a string of characters

        Args:
            text (str): The text to type
        """
        for char in text:
            key_code = ord(char.lower())
            self.type_key(key_code)
            time.sleep(0.1)  # Small delay between keypresses

    def send_mouse(self, x, y, button_mask=0):
        """
        Send mouse event to specific coordinates

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            button_mask (int): Button state mask (0=no buttons, 1=left, 2=middle, 4=right)
        """
        js_code = f"window.guacClient.sendMouseState({{ x: {x}, y: {y}, left: {str(bool(button_mask & 1)).lower()}, middle: {str(bool(button_mask & 2)).lower()}, right: {str(bool(button_mask & 4)).lower()} }});"
        self.driver.execute_script(js_code)


def take_screenshot(url):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(10)  # Wait for page to load

        # Create automation instance
        guac = GuacamoleAutomation(driver)

        # Example: Type 'aaa' using our new methods
        guac.type_string("aaa")

        # Wait and take screenshot
        time.sleep(2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        driver.save_screenshot(filename)
        print(f"Screenshot saved as {filename}")

    finally:
        driver.quit()
