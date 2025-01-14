from abc import ABCMeta, abstractmethod
from typing import Tuple
import logging
from ..tools.base_tool import ToolError


LOGGER = logging.getLogger(__name__)


class ComputerUseExecutor(metaclass=ABCMeta):
    """Abstract base class for controlling a computer."""

    def __init__(self, typing_delay_ms=12):
        self.typing_delay_ms = typing_delay_ms

    @abstractmethod
    def key(self, key: str) -> None:
        """Press a key or key-combination on the keyboard."""
        ...

    @abstractmethod
    def type(self, text: str) -> None:
        """Type a string of text on the keyboard."""
        ...

    @abstractmethod
    def cursor_position(self) -> Tuple[int, int]:
        """Get the current (x, y) pixel coordinate of the cursor on the screen."""
        ...

    @abstractmethod
    def mouse_move(self, x: int, y: int) -> None:
        """Move the cursor to a specified (x, y) pixel coordinate on the screen."""
        ...

    @abstractmethod
    def left_click(self) -> None:
        """Click the left mouse button."""
        ...

    @abstractmethod
    def left_click_drag(self, x: int, y: int) -> None:
        """Click and drag the cursor to a specified (x, y) pixel coordinate on the screen."""
        ...

    @abstractmethod
    def right_click(self) -> None:
        """Click the right mouse button."""
        ...

    @abstractmethod
    def middle_click(self) -> None:
        """Click the middle mouse button."""
        ...

    @abstractmethod
    def double_click(self) -> None:
        """Double-click the left mouse button."""
        ...

    @abstractmethod
    def screenshot(self) -> str:
        """Take a screenshot of the screen. Returns the base64-encoded image."""
        ...

    def validate_action(
        self, action: str, text: str, coordinate: Tuple[int, int]
    ) -> None:
        """Validate the action and its parameters."""

        match action:
            case "mouse_move" | "left_click_drag":
                self.require_coordinate(coordinate)
                self.require_not_text(text)
            case "key" | "type":
                self.require_text(text)
                self.require_not_coordinate(coordinate)
            case (
                "left_click"
                | "right_click"
                | "double_click"
                | "middle_click"
                | "screenshot"
                | "cursor_position"
            ):
                self.require_not_text(text)
                self.require_not_coordinate(coordinate)
            case _:
                raise ToolError(f"Could not validate invalid action: '{action}'")

    def require_text(self, text: str) -> None:
        """Raise an error if the text is None."""
        if text is None:
            raise ToolError("Text is required for this action.")

        if not isinstance(text, str):
            raise ToolError(output=f"{text} must be a string")

    def require_not_text(self, text: str) -> None:
        """Raise an error if the text is not None."""
        if text is not None:
            raise ToolError("Text is not accepted for this action.")

    def require_coordinate(self, coordinate: Tuple[int, int]) -> None:
        """Raise an error if the coordinate is None."""
        if coordinate is None:
            raise ToolError("Coordinate is required for this action.")

        if not isinstance(coordinate, list) or len(coordinate) != 2:
            raise ToolError(f"{coordinate} must be a tuple of length 2")

        if not all(isinstance(i, int) and i >= 0 for i in coordinate):
            raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

    def require_not_coordinate(self, coordinate: Tuple[int, int]) -> None:
        """Raise an error if the coordinate is not None."""
        if coordinate is not None:
            raise ToolError("Coordinate is not accepted for this action.")
