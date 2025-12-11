# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0


def extract_prompt_id(message: str) -> tuple[str, str]:
  """
  Extract prompt_id from a message string if present.

  Args:
      message (str): The message potentially containing a prompt_id delimiter.

  Returns:
      tuple[str, str]: A tuple of (cleaned_message, prompt_id).
                      If no prompt_id found, returns (original_message, "").

  Examples:
      >>> extract_prompt_id("What is inventory?[prompt-id:123]")
      ("What is inventory?", "123")
      >>> extract_prompt_id("Regular message")
      ("Regular message", "")
  """
  import re

  # Pattern matches [prompt-id: <uuid>] or [prompt-id:<uuid>]
  pattern = r'\[prompt-id:\s*([a-f0-9-]+)\]'
  match = re.search(pattern, message, re.IGNORECASE)

  if match:
    prompt_id = match.group(1)
    cleaned_message = re.sub(pattern, '', message, flags=re.IGNORECASE).strip()
    return cleaned_message, prompt_id

  return message, ""


def inject_prompt_id(message: str, prompt_id: str) -> str:
  """
  Inject a prompt_id into a message string.

  Args:
      message (str): The base message.
      prompt_id (str): The prompt_id to inject.

  Returns:
      str: The message with prompt_id appended.

  Examples:
      >>> inject_prompt_id("What is inventory?", "123-456")
      "What is inventory?[prompt-id:123-456]"
  """
  if not prompt_id:
    return message

  return f"{message}[prompt-id:{prompt_id}]"