# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Cache configuration from environment variables.

Environment Variables:
    CACHE_ENABLED: Enable/disable all caching ("true"/"false", default: "true")
    CACHE_MODE: Cache mode - "tool", "none" (default: "tool")

    TOOL_CACHE_TTL: Tool cache TTL in seconds (default: 600)
    TOOL_CACHE_MAX_ENTRIES: Tool cache max entries (default: 500)
    TOOL_CACHE_EXCLUDE: Comma-separated list of tools to NOT cache (default: none excluded)
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set

from agent_recruiter.common.logging import get_logger

logger = get_logger("plugins.cache_config")


class CacheMode(Enum):
    """Cache mode options."""
    NONE = "none"
    TOOL = "tool"


@dataclass
class ToolCacheConfig:
    """Configuration for tool-level caching."""
    enabled: bool
    ttl_seconds: int
    max_entries: int
    excluded_tools: Set[str]  # Tools to NOT cache (empty set means cache all)


@dataclass
class CacheConfig:
    """Combined cache configuration."""
    mode: CacheMode
    tool: ToolCacheConfig

    @property
    def tool_cache_enabled(self) -> bool:
        """Check if tool caching is enabled based on mode."""
        return self.mode in (CacheMode.TOOL,) and self.tool.enabled


def _parse_bool(value: str, default: bool = True) -> bool:
    """Parse a boolean from environment variable string."""
    if not value:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _parse_int(value: str, default: int) -> int:
    """Parse an integer from environment variable string."""
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid integer value '{value}', using default {default}")
        return default


def _parse_excluded_tools(value: str) -> Set[str]:
    """Parse a comma-separated list of tool names to exclude from caching.

    Returns empty set if value is empty (meaning cache all tools).
    """
    if not value:
        return set()

    return {t.strip() for t in value.split(",") if t.strip()}


def _parse_cache_mode(value: str) -> CacheMode:
    """Parse cache mode from environment variable."""
    if not value:
        return CacheMode.TOOL

    try:
        return CacheMode(value.lower())
    except ValueError:
        valid_modes = [m.value for m in CacheMode]
        logger.warning(
            f"Invalid CACHE_MODE '{value}', valid options: {valid_modes}. "
            f"Using default 'tool'"
        )
        return CacheMode.TOOL


def load_cache_config() -> CacheConfig:
    """Load cache configuration from environment variables.

    Returns:
        CacheConfig with all settings populated from env vars or defaults.
    """
    # Global enable/disable
    global_enabled = _parse_bool(os.getenv("CACHE_ENABLED", "true"))
    cache_mode = _parse_cache_mode(os.getenv("CACHE_MODE", "tool"))

    # If globally disabled, set mode to NONE
    if not global_enabled:
        cache_mode = CacheMode.NONE

    # Tool cache settings
    tool_config = ToolCacheConfig(
        enabled=_parse_bool(os.getenv("TOOL_CACHE_ENABLED", "true")),
        ttl_seconds=_parse_int(os.getenv("TOOL_CACHE_TTL", ""), 600),
        max_entries=_parse_int(os.getenv("TOOL_CACHE_MAX_ENTRIES", ""), 500),
        excluded_tools=_parse_excluded_tools(os.getenv("TOOL_CACHE_EXCLUDE", "")),
    )

    config = CacheConfig(
        mode=cache_mode,
        tool=tool_config,
    )

    logger.info(
        f"Cache config loaded: mode={cache_mode.value}, "
        f"tool_enabled={config.tool_cache_enabled}"
    )

    return config


# Default tools to EXCLUDE from caching (empty = cache all tools)
# Add tools here that have side effects or should not be cached
DEFAULT_EXCLUDED_TOOLS: Set[str] = {"store_search_results"}
