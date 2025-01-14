"""
Agentic sampling loop that calls the Anthropic API and local implementation of
anthropic-defined computer use tools.
"""

from typing import Callable
from anthropic import (
    AnthropicBedrock,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)
from time import sleep

from .tools import ToolBox, ToolResult
from .system_prompt import SYSTEM_PROMPT
import logging

LOGGER = logging.getLogger(__name__)

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"


def perform_action(
    *,
    anthropic_client: AnthropicBedrock,
    model: str,
    action_description: str,
    toolbox: ToolBox,
    max_tokens: int = 4096,
    system_prompt_suffix: str = "",
    only_n_most_recent_images: int = 0,
    previous_messages: list[BetaMessageParam] | None = None,
    on_new_message_callback: Callable | None = None,
):
    """Perform an arbitrary action on a computer using the Anthropic API.

    Parameters:
    -----------
    anthropic_client : AnthropicBedrock
        The Anthropic client to use.
    model : str
        The model to use for the API call.
    action_description : str
        The action to perform in plain english.
    toolbox : ToolBox
        The collection of tools that the assistant can use.
    max_tokens : int, optional
        The maximum number of output tokens to generate.
    system_prompt_suffix : str, optional
        The suffix to append to the system prompt.
    only_n_most_recent_images : int, optional
        The number of most recent images to keep in the prompt cache.
    previous_messages : list[BetaMessageParam], optional
        The previous messages to use as context for the API call.
    on_new_message_callback : Callable, optional
        A callback function to call when a new message is received.
    """
    messages = previous_messages or []

    if not on_new_message_callback:
        on_new_message_callback = lambda _: None
    system = BetaTextBlockParam(type="text", text=SYSTEM_PROMPT + system_prompt_suffix)

    initial_message = {
        "role": "user",
        "content": [BetaTextBlockParam(type="text", text=action_description)],
    }
    messages.append(initial_message)
    on_new_message_callback(initial_message)

    while True:
        # Prune images to only keep the most recent N images
        if only_n_most_recent_images > 0:
            filter_to_n_most_recent_images(
                messages,
                only_n_most_recent_images,
                min_removal_threshold=only_n_most_recent_images,
            )

        # Send messages to the API
        try:
            response = anthropic_client.beta.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=[system],
                tools=toolbox.to_params(),
                betas=[COMPUTER_USE_BETA_FLAG],
            )
        except (APIError, APIStatusError, APIResponseValidationError) as e:
            LOGGER.error(f"API error: {e}")
            return messages

        response_params = response_to_params(response)
        message = {"role": "assistant", "content": response_params}
        messages.append(message)
        on_new_message_callback(message)

        # Run tools locally, if needed
        tool_result: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            if content_block["type"] == "tool_use":
                tool_name = content_block["name"]
                tool_input = content_block["input"]
                result = toolbox.run(name=tool_name, tool_input=tool_input)
                result = make_api_tool_result(result, content_block["id"])
                tool_result.append(result)

        # No tool results means that the assistant believes it has finished the task
        if not tool_result:
            return messages

        message = {"role": "user", "content": tool_result}
        messages.append(message)
        on_new_message_callback(message)
        sleep(1.5)


def filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int,
):
    """
    Keeps only the most recent N images from tool results, removing older ones in chunks
    of min_removal_threshold size to preserve prompt cache efficiency.
    """
    # Extract all tool results that contain images
    tool_results = []
    for message in messages:
        content_items = message.get("content", [])
        if not isinstance(content_items, list):
            continue

        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                tool_results.append(item)

    # Count total images
    image_count = sum(
        1
        for result in tool_results
        for content in result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )

    # Calculate how many images to remove, rounded to threshold
    images_to_remove = image_count - images_to_keep
    images_to_remove -= images_to_remove % min_removal_threshold

    if images_to_remove <= 0:
        return messages

    # Remove oldest images while preserving non-image content
    remaining_to_remove = images_to_remove
    for tool_result in tool_results:
        if not isinstance(tool_result.get("content"), list):
            continue

        tool_result["content"] = [
            content
            for content in tool_result["content"]
            if not (
                isinstance(content, dict)
                and content.get("type") == "image"
                and remaining_to_remove > 0
                and not (remaining_to_remove := remaining_to_remove - 1)
            )
        ]

    return messages


def response_to_params(response: BetaMessage):
    result = []

    for block in response.content:
        if isinstance(block, BetaTextBlock):
            result.append({"type": "text", "text": block.text})
        else:
            result.append(block.model_dump())

    return result


def make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""

    result_text = f"<system>{result.system}</system>\n" if result.system else ""

    if result.error:
        return BetaToolResultBlockParam(
            tool_use_id=tool_use_id,
            type="tool_result",
            content=result_text + result.error,
            is_error=True,
        )

    tool_result = []

    if result.base64_image:
        tool_result.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image,
                },
            }
        )

    return BetaToolResultBlockParam(
        tool_use_id=tool_use_id,
        type="tool_result",
        content=tool_result,
        is_error=False,
    )
