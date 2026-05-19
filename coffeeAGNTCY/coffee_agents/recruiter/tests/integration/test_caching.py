# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for response and tool caching.

Run with: pytest tests/integration/test_caching.py -v
"""

import pytest
from agent_recruiter.recruiter import RecruiterTeam
from google.adk.agents.invocation_context import LlmCallsLimitExceededError


@pytest.fixture
def recruiter_team():
    """Create a RecruiterTeam with caching enabled."""
    return RecruiterTeam()


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
        """Second invoke of the same prompt should reuse tool results via the cache.

        We assert cache *semantics*, not wall-clock timing: ADK caching is working
        iff the second invoke produces hits without adding a full second round of
        misses. Timing-based assertions here were flaky on CI (model variance,
        cold imports, shared runners) and didn't actually test the cache.
        """
        user_id = "test_user"
        message = "What skills can I search upon the agent registry with?"

        await recruiter_team.invoke(message, user_id, "timing_session_1")
        stats1 = recruiter_team.get_cache_stats()["tool_cache"]
        assert stats1, "Tool cache must be enabled for this test"
        misses1, hits1 = stats1["misses"], stats1["hits"]
        assert misses1 > 0, "Expected at least one cache miss on first request"

        await recruiter_team.invoke(message, user_id, "timing_session_2")
        stats2 = recruiter_team.get_cache_stats()["tool_cache"]
        misses2, hits2 = stats2["misses"], stats2["hits"]

        assert hits2 > hits1, (
            f"Expected new cache hits on second request "
            f"(hits {hits1} -> {hits2})"
        )
        assert misses2 - misses1 < misses1, (
            f"Second invoke should add fewer new misses than first cold run "
            f"(first={misses1}, added={misses2 - misses1})"
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
