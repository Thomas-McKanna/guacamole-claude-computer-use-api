from .executor_base import ComputerUseExecutor
from typing import Any, Tuple
from selenium.webdriver.chrome.webdriver import WebDriver
import logging
from time import sleep
from enum import Enum
from ..keysym_lookup import KEYSYM_MAP

LOGGER = logging.getLogger(__name__)


class GuacamoleExecutor(ComputerUseExecutor):
    class KeyAction(Enum):
        KEY_DOWN = 1
        KEY_UP = 0

    class MouseButton(Enum):
        MOUSE_LEFT = 1
        MOUSE_MIDDLE = 2
        MOUSE_RIGHT = 4

    def __init__(self, driver: WebDriver, typing_delay_ms=50):
        super().__init__(typing_delay_ms)
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

    def key(self, key: str) -> None:
        key_codes = self._key_to_codes(key)

        if not key_codes:
            return

        js = ""

        # Press all keys in the order they appear
        for key_code in key_codes:
            js += self._get_key_action_js(key_code, self.KeyAction.KEY_DOWN)

        # Release all keys in the reverse order
        for key_code in reversed(key_codes):
            js += self._get_key_action_js(key_code, self.KeyAction.KEY_UP)

        self.driver.execute_script(js)

    def type(self, text: str) -> None:
        for char in text:
            self.key(char)
            sleep(self.typing_delay_ms / 1000)

    def cursor_position(self) -> Tuple[int, int]:
        x = self.driver.execute_script("return window.guacClient.getDisplay().cursorX;")
        y = self.driver.execute_script("return window.guacClient.getDisplay().cursorY;")
        return x, y

    def mouse_move(self, x: int, y: int) -> None:
        js = self._get_mouse_action_js(x, y, 0)
        self.driver.execute_script(js)

    def left_click(self) -> None:
        no_pressed_buttons = 0
        pressed_buttons = self.MouseButton.MOUSE_LEFT.value
        js = self._get_mouse_action_js(*self.cursor_position(), pressed_buttons)
        js += self._get_mouse_action_js(*self.cursor_position(), no_pressed_buttons)
        self.driver.execute_script(js)

    def left_click_drag(self, x: int, y: int) -> None:
        no_pressed_buttons = 0
        pressed_buttons = self.MouseButton.MOUSE_LEFT.value
        js = self._get_mouse_action_js(*self.cursor_position(), pressed_buttons)
        js += self._get_mouse_action_js(x, y, pressed_buttons)
        js += self._get_mouse_action_js(x, y, no_pressed_buttons)
        self.driver.execute_script(js)

    def right_click(self) -> None:
        no_pressed_buttons = 0
        pressed_buttons = self.MouseButton.MOUSE_RIGHT.value
        js = self._get_mouse_action_js(*self.cursor_position(), pressed_buttons)
        js += self._get_mouse_action_js(*self.cursor_position(), no_pressed_buttons)
        self.driver.execute_script(js)

    def middle_click(self) -> None:
        no_pressed_buttons = 0
        pressed_buttons = self.MouseButton.MOUSE_MIDDLE.value
        js = self._get_mouse_action_js(*self.cursor_position(), pressed_buttons)
        js += self._get_mouse_action_js(*self.cursor_position(), no_pressed_buttons)
        self.driver.execute_script(js)

    def double_click(self) -> None:
        self.left_click()
        self.left_click()

    def screenshot(self) -> str:
        return self.driver.get_screenshot_as_base64()

    def _get_key_press_js(self, key_code: int) -> str:
        result = self._get_key_action_js(key_code, self.KeyAction.KEY_DOWN)
        result += self._get_key_action_js(key_code, self.KeyAction.KEY_UP)
        return result

    def _get_key_action_js(self, key_code: int, action: KeyAction) -> str:
        return f"window.guacClient.sendKeyEvent({action.value}, {key_code});"

    def _get_mouse_action_js(self, x: int, y: int, pressed_button_mask: int) -> str:
        return f"""window.guacClient.sendMouseState(
            {{ x: {x}, y: {y},
               left: {str(bool(pressed_button_mask & 1)).lower()},
               middle: {str(bool(pressed_button_mask & 2)).lower()},
               right: {str(bool(pressed_button_mask & 4)).lower()}
            }});"""

    def _key_to_codes(self, key: str) -> list[int]:
        keys = key.split("+")

        result = []

        for key in keys:
            try:
                key_code = KEYSYM_MAP[key]
            except KeyError:
                LOGGER.debug(f"Key not found in KEYSYM_MAP: {key}")
                continue

            result.append(key_code)

        return result
