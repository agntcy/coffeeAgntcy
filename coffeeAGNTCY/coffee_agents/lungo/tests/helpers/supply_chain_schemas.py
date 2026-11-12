# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Checks of a JSON schema against Azure OpenAI strict structured output."""

from __future__ import annotations

from typing import Any

# Keywords that Azure strict mode does not accept, as far as we have seen.
UNSUPPORTED = {"exclusiveMinimum", "exclusiveMaximum", "minimum", "maximum"}


def _walk(node: Any, path: str = "#"):
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            yield from _walk(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{path}/{index}")


def strict_violations(schema: dict[str, Any]) -> list[str]:
    """Every place where ``schema`` is not valid for strict structured output."""
    found = []
    for path, node in _walk(schema):
        properties = node.get("properties")
        if isinstance(properties, dict) and "type" in node:
            missing = set(properties) - set(node.get("required", []))
            if missing:
                found.append(f"{path}: not required: {sorted(missing)}")
        for keyword in UNSUPPORTED & node.keys():
            if path.rsplit("/", 1)[-1] != "properties":
                found.append(f"{path}: unsupported keyword {keyword}")
    return found
