# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for response and tool caching.

Run with: pytest test/integration/test_caching.py -v
"""

import asyncio
import time
import pytest
from agent_recruiter.recruiter import RecruiterTeam


@pytest.fixture
def recruiter_team():
    """Create a RecruiterTeam with caching enabled."""
    return RecruiterTeam()


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

class TestToolCaching:
    """Tests for tool-level caching."""

    @pytest.mark.asyncio
    async def test_tool_cache_hit_on_repeated_search(self, recruiter_team):
        """Same search query should hit tool cache when using different sessions."""
        user_id = "test_user"
        message = "What skills can I search upon the agent registry with?"

        # First request - populates cache
        await recruiter_team.invoke(message, user_id, "cache_test_session_1")
        stats1 = recruiter_team.get_cache_stats()

        tool_hits1 = stats1["tool_cache"]["hits"] if stats1["tool_cache"] else 0
        tool_misses1 = stats1["tool_cache"]["misses"] if stats1["tool_cache"] else 0
        print(f"\nFirst request - Tool cache: hits={tool_hits1}, misses={tool_misses1}")

        # Second request with DIFFERENT session so LLM must call tools again
        # (same session would have answer in context, so LLM wouldn't call tools)
        await recruiter_team.invoke(message, user_id, "cache_test_session_2")
        stats2 = recruiter_team.get_cache_stats()

        tool_hits2 = stats2["tool_cache"]["hits"] if stats2["tool_cache"] else 0
        print(f"Second request - Tool cache hits: {tool_hits2}")

        # Tool cache should have hits if the same tool was called with same args
        if tool_misses1 > 0:  # Only check if tools were actually called
            assert tool_hits2 > tool_hits1, (
                f"Expected tool cache hits on repeated search. "
                f"Before: {tool_hits1}, After: {tool_hits2}"
            )

    @pytest.mark.asyncio
    async def test_cache_hit_reduces_operation_time(self, recruiter_team):
        """Cache hits should reduce operation time compared to cache misses."""
        user_id = "test_user"
        message = "What skills can I search upon the agent registry with?"

        # First request - cache miss, should be slower
        # Use a unique session so the LLM must call tools
        start_time = time.perf_counter()
        await recruiter_team.invoke(message, user_id, "timing_session_1")
        first_request_time = time.perf_counter() - start_time

        stats1 = recruiter_team.get_cache_stats()
        tool_misses = stats1["tool_cache"]["misses"] if stats1["tool_cache"] else 0

        print(f"\nFirst request time: {first_request_time:.3f}s (cache misses: {tool_misses})")

        # Only run timing assertion if tools were actually called and cached
        if tool_misses == 0:
            pytest.skip("No tool cache misses - cannot verify timing improvement")

        # Second request - use a DIFFERENT session so LLM doesn't have answer in context
        # This forces tool calls, which should now hit the cache
        start_time = time.perf_counter()
        await recruiter_team.invoke(message, user_id, "timing_session_2")
        second_request_time = time.perf_counter() - start_time

        stats2 = recruiter_team.get_cache_stats()
        tool_hits = stats2["tool_cache"]["hits"] if stats2["tool_cache"] else 0

        print(f"Second request time: {second_request_time:.3f}s (cache hits: {tool_hits})")
        print(f"Time reduction: {first_request_time - second_request_time:.3f}s "
              f"({((first_request_time - second_request_time) / first_request_time * 100):.1f}%)")

        # Assert cache was hit (with different session, LLM must call tools again)
        assert tool_hits > 0, "Expected cache hits on second request with different session"

        # Assert second request was faster due to cache hits
        assert second_request_time < first_request_time, (
            f"Expected cached request to be faster. "
            f"First: {first_request_time:.3f}s, Second: {second_request_time:.3f}s"
        )


class TestCacheStatistics:
    """Tests for cache statistics reporting."""

    def test_cache_stats_structure(self, recruiter_team):
        """Cache stats should have expected structure."""
        stats = recruiter_team.get_cache_stats()

        assert "mode" in stats, "Stats should include cache mode"
        assert "tool_cache" in stats, "Stats should include tool_cache"

        if stats["tool_cache"]:
            tc = stats["tool_cache"]
            assert "hits" in tc
            assert "misses" in tc
            assert "skipped" in tc
            assert "hit_rate_percent" in tc
            assert "cache_size" in tc
            assert "excluded_tools" in tc

    @pytest.mark.asyncio
    async def test_clear_cache(self, recruiter_team):
        """Clearing cache should reset cache size."""
        user_id = "test_user"
        session_id = "clear_test"
        message = "What skills can I search upon the agent registry with?"

        # Make a request to populate cache
        await recruiter_team.invoke(message, user_id, session_id)

        stats_before = recruiter_team.get_cache_stats()
        tool_size_before = stats_before["tool_cache"]["cache_size"] if stats_before["tool_cache"] else 0

        # Clear cache
        cleared = recruiter_team.clear_cache()
        print(f"\nCleared: {cleared}")

        stats_after = recruiter_team.get_cache_stats()
        tool_size_after = stats_after["tool_cache"]["cache_size"] if stats_after["tool_cache"] else 0

        assert tool_size_after == 0, "Tool cache should be empty after clearing"
        if tool_size_before > 0:
            assert cleared["tool_cache_cleared"] > 0, "Should report entries cleared"


class TestCacheConfiguration:
    """Tests for cache configuration."""

    def test_cache_disabled(self):
        """Test that caching can be disabled."""
        import os

        # Save original value
        original = os.environ.get("CACHE_MODE")

        try:
            os.environ["CACHE_MODE"] = "none"

            # Need to reload config
            from agent_recruiter.plugins.cache_config import load_cache_config
            config = load_cache_config()

            assert not config.tool_cache_enabled
        finally:
            # Restore original value
            if original:
                os.environ["CACHE_MODE"] = original
            else:
                os.environ.pop("CACHE_MODE", None)

    def test_tool_mode(self):
        """Test tool cache mode (default)."""
        import os

        original = os.environ.get("CACHE_MODE")

        try:
            os.environ["CACHE_MODE"] = "tool"

            from agent_recruiter.plugins.cache_config import load_cache_config
            config = load_cache_config()

            assert config.tool_cache_enabled
        finally:
            if original:
                os.environ["CACHE_MODE"] = original
            else:
                os.environ.pop("CACHE_MODE", None)

    def test_excluded_tools_config(self):
        """Test that excluded tools can be configured via environment."""
        import os

        original = os.environ.get("TOOL_CACHE_EXCLUDE")

        try:
            os.environ["TOOL_CACHE_EXCLUDE"] = "tool_a,tool_b,tool_c"

            from agent_recruiter.plugins.cache_config import load_cache_config
            config = load_cache_config()

            assert "tool_a" in config.tool.excluded_tools
            assert "tool_b" in config.tool.excluded_tools
            assert "tool_c" in config.tool.excluded_tools
        finally:
            if original:
                os.environ["TOOL_CACHE_EXCLUDE"] = original
            else:
                os.environ.pop("TOOL_CACHE_EXCLUDE", None)
