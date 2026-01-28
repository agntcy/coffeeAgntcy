# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Tool-level caching plugin for ADK agents.

This plugin caches tool execution results to avoid redundant
operations like repeated registry searches.
"""

import hashlib
import json
import time
from typing import Any, Optional, Set
from collections import OrderedDict

from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from agent_recruiter.common.logging import get_logger

logger = get_logger("plugins.tool_cache")


class ToolCachePlugin(BasePlugin):
    """Cache tool execution results with TTL and LRU eviction.

    This plugin intercepts tool calls and returns cached results
    when available, skipping expensive operations like API calls
    or database queries.

    Attributes:
        ttl_seconds: Time-to-live for cache entries in seconds.
        max_entries: Maximum number of entries before LRU eviction.
        excluded_tools: Set of tool names to NOT cache (empty = cache all).
    """

    def __init__(
        self,
        ttl_seconds: int = 600,
        max_entries: int = 500,
        excluded_tools: Optional[Set[str]] = None,
        enabled: bool = True
    ):
        """Initialize the tool cache plugin.

        Args:
            ttl_seconds: Cache entry lifetime (default: 10 minutes).
            max_entries: Max cache size before eviction (default: 500).
            excluded_tools: Set of tool names to NOT cache. If None or empty, caches all tools.
                           Example: {"send_email", "create_user"}  # tools with side effects
            enabled: Whether caching is active (default: True).
        """
        super().__init__(name="tool_cache")
        self._cache: OrderedDict[str, tuple[dict, float]] = OrderedDict()
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._excluded_tools = excluded_tools or set()
        self._enabled = enabled

        # Stats for monitoring
        self._hits = 0
        self._misses = 0
        self._skipped = 0  # Tools in excluded_tools set

    def _should_cache_tool(self, tool_name: str) -> bool:
        """Check if a tool should be cached.

        Args:
            tool_name: Name of the tool.

        Returns:
            True if the tool should be cached (not in excluded set).
        """
        return tool_name not in self._excluded_tools

    def _cache_key(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        """Generate a deterministic cache key from tool name and args.

        Args:
            tool_name: Name of the tool being called.
            tool_args: Arguments passed to the tool.

        Returns:
            A SHA-256 hash string representing the tool call.
        """
        # Serialize args in a deterministic way
        try:
            args_str = json.dumps(tool_args, sort_keys=True, default=str)
        except (TypeError, ValueError):
            # Fallback for non-serializable args
            args_str = str(sorted(tool_args.items()))

        combined = f"{tool_name}:{args_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _evict_expired(self) -> int:
        """Remove expired entries from the cache.

        Returns:
            Number of entries evicted.
        """
        now = time.time()
        expired_keys = [
            k for k, (_, timestamp) in self._cache.items()
            if now - timestamp >= self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Evicted {len(expired_keys)} expired tool cache entries")

        return len(expired_keys)

    def _evict_lru(self) -> None:
        """Evict least recently used entries if cache exceeds max size."""
        while len(self._cache) >= self._max_entries:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug(f"LRU evicted tool cache entry: {evicted_key[:16]}...")

    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[dict]:
        """Check cache before executing a tool.

        If a cached result exists for this tool call, return it immediately
        to skip the actual tool execution.

        Args:
            tool: The tool being called.
            tool_args: Arguments for the tool.
            tool_context: ADK tool context.

        Returns:
            Cached result dict if available, None otherwise.
        """
        if not self._enabled:
            return None

        tool_name = tool.name if hasattr(tool, 'name') else str(tool)

        # Check if this tool should be cached
        if not self._should_cache_tool(tool_name):
            self._skipped += 1
            return None

        # Clean up expired entries periodically
        self._evict_expired()

        key = self._cache_key(tool_name, tool_args)

        if key in self._cache:
            result, timestamp = self._cache[key]

            # Check if still valid
            if time.time() - timestamp < self._ttl:
                self._hits += 1
                # Move to end to mark as recently used
                self._cache.move_to_end(key)
                logger.info(
                    f"Tool cache HIT: {tool_name} (key={key[:16]}..., "
                    f"hits={self._hits}, misses={self._misses})"
                )
                return result
            else:
                # Entry expired
                del self._cache[key]

        self._misses += 1
        logger.debug(
            f"Tool cache MISS: {tool_name} (key={key[:16]}..., "
            f"Tool arguments: {tool_args}, "
            f"hits={self._hits}, misses={self._misses})"
        )
        return None

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict
    ) -> Optional[dict]:
        """Store the tool result in cache after successful execution.

        Args:
            tool: The tool that was called.
            tool_args: Arguments passed to the tool.
            tool_context: ADK tool context.
            result: The result from the tool execution.

        Returns:
            None (result passes through unchanged).
        """
        if not self._enabled:
            return None

        tool_name = tool.name if hasattr(tool, 'name') else str(tool)

        # Check if this tool should be cached
        if not self._should_cache_tool(tool_name):
            return None

        # Don't cache error results
        if isinstance(result, dict) and result.get("error"):
            logger.debug(f"Skipping cache for error result from {tool_name}")
            return None

        key = self._cache_key(tool_name, tool_args)

        # Ensure we don't exceed max entries
        self._evict_lru()

        # Store result with current timestamp
        self._cache[key] = (result, time.time())
        logger.debug(
            f"Cached tool result: {tool_name} (key={key[:16]}..., "
            f"cache_size={len(self._cache)})"
        )

        return None

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with hit/miss counts, hit rate, and cache size.
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "skipped": self._skipped,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._cache),
            "max_entries": self._max_entries,
            "ttl_seconds": self._ttl,
            "excluded_tools": list(self._excluded_tools) if self._excluded_tools else [],
            "enabled": self._enabled,
        }

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Tool cache cleared ({count} entries removed)")
        return count

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable caching at runtime.

        Args:
            enabled: Whether to enable caching.
        """
        self._enabled = enabled
        logger.info(f"Tool cache {'enabled' if enabled else 'disabled'}")

    def exclude_tool(self, tool_name: str) -> None:
        """Add a tool to the excluded tools set (stop caching it).

        Args:
            tool_name: Name of the tool to exclude from caching.
        """
        self._excluded_tools.add(tool_name)
        logger.debug(f"Excluded '{tool_name}' from caching")

    def include_tool(self, tool_name: str) -> None:
        """Remove a tool from the excluded set (start caching it).

        Args:
            tool_name: Name of the tool to start caching.
        """
        self._excluded_tools.discard(tool_name)
        logger.debug(f"Removed '{tool_name}' from exclusion list")
