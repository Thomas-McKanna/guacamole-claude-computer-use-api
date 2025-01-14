from typing import Literal, TypedDict

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base_tool import BaseAnthropicTool, ToolError, ToolResult
from ..executors.executor_base import ComputerUseExecutor


Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]


class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None


class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of
    the current computer. The tool parameters are defined by Anthropic and are not
    editable.

    See https://docs.anthropic.com/en/docs/build-with-claude/computer-use#computer-tool
    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 2.0
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": self.display_num,
        }

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        executor: ComputerUseExecutor,
    ):
        super().__init__()
        self.width = screen_width
        self.height = screen_height
        self.executor = executor
        self.display_num = None  # Not used

    def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        self.executor.validate_action(action, text, coordinate)

        match action:
            case "mouse_move":
                self.executor.mouse_move(*coordinate)
            case "left_click_drag":
                self.executor.left_click_drag(*coordinate)
            case "key":
                self.executor.key(text)
            case "type":
                self.executor.type(text)
            case "left_click":
                self.executor.left_click()
            case "right_click":
                self.executor.right_click()
            case "middle_click":
                self.executor.middle_click()
            case "double_click":
                self.executor.double_click()
            case "cursor_position":
                self.executor.cursor_position()
            case "screenshot":
                pass  # Screenshot will always be taken after the action
            case _:
                raise ToolError(f"Could not execute invalid action: {action}")

        return ToolResult(base64_image=self.executor.screenshot())

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}
