# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for response and tool caching.

Run with: pytest tests/integration/test_caching.py -v
"""

import asyncio
import time

import pytest
from agent_recruiter.recruiter import RecruiterTeam


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
    async def test_cache_hit_reduces_operation_time(self, recruiter_team, monkeypatch):
        """Cache hits should reduce time spent on miss-path work (not dominated by LLM variance).

        Miss-path CPU work runs in a thread pool so it does not block the asyncio event loop.
        Blocking the loop here previously stalled ADK/genai I/O and looked like repeated LLM calls in CI.
        """
        user_id = "test_user"
        message = "What skills can I search upon the agent registry with?"
        plugin = recruiter_team._tool_cache_plugin
        assert plugin is not None, "Tool cache plugin must be enabled for this test"

        work_calls = 0
        miss_penalty_first = 0.0
        miss_penalty_second = 0.0
        phase = "first"

        # Enough work to measure miss vs hit reliably without multi-minute runs on slow CI CPUs.
        work_iterations = 2_500_000

        def expensive_work(iterations: int) -> int:
            """Deterministic miss-path CPU work (runs off the event loop)."""
            nonlocal work_calls
            work_calls += 1
            checksum = 0
            for i in range(iterations):
                checksum ^= (i * 2654435761) & 0xFFFFFFFF
            return checksum

        original_before_tool_callback = plugin.before_tool_callback

        async def wrapped_before_tool_callback(*, tool, tool_args, tool_context):
            nonlocal miss_penalty_first, miss_penalty_second
            misses_before = plugin.get_stats()["misses"]
            cached = await original_before_tool_callback(
                tool=tool, tool_args=tool_args, tool_context=tool_context
            )
            misses_after = plugin.get_stats()["misses"]
            if misses_after > misses_before:
                t0 = time.perf_counter()
                await asyncio.to_thread(expensive_work, work_iterations)
                dt = time.perf_counter() - t0
                if phase == "first":
                    miss_penalty_first += dt
                else:
                    miss_penalty_second += dt
            return cached

        monkeypatch.setattr(plugin, "before_tool_callback", wrapped_before_tool_callback)

        # First request: miss-heavy path with deterministic miss penalty.
        start_time = time.perf_counter()
        await recruiter_team.invoke(message, user_id, "timing_session_1")
        first_request_time = time.perf_counter() - start_time
        stats1 = recruiter_team.get_cache_stats()
        tool_hits1 = stats1["tool_cache"]["hits"] if stats1["tool_cache"] else 0
        tool_misses1 = stats1["tool_cache"]["misses"] if stats1["tool_cache"] else 0

        print(f"\nFirst request time: {first_request_time:.3f}s (cache misses: {tool_misses1})")

        phase = "second"
        # Second request: hit-heavy path should avoid most miss penalty.
        start_time = time.perf_counter()
        await recruiter_team.invoke(message, user_id, "timing_session_2")
        second_request_time = time.perf_counter() - start_time
        stats2 = recruiter_team.get_cache_stats()
        tool_hits2 = stats2["tool_cache"]["hits"] if stats2["tool_cache"] else 0
        tool_misses2 = stats2["tool_cache"]["misses"] if stats2["tool_cache"] else 0

        print(f"Second request time: {second_request_time:.3f}s (cache hits: {tool_hits2})")
        print(
            f"Miss-path CPU time: first={miss_penalty_first:.3f}s, second={miss_penalty_second:.3f}s"
        )

        # Assert cache semantics and structural behavior.
        assert tool_misses1 > 0, "Expected at least one cache miss on first request"
        assert tool_hits2 > tool_hits1, "Expected additional cache hits on second request"
        assert tool_misses2 >= tool_misses1, "Miss counter should be monotonic"
        assert work_calls > 0, "Expected deterministic overhead to run on misses"
        assert work_calls == tool_misses2, (
            "Expected miss-only overhead to run once per cache miss callback"
        )

        assert miss_penalty_first > 0.05, "Expected measurable miss-path work on first request"

        new_misses = tool_misses2 - tool_misses1
        # Same prompt usually reuses many tools; cache should add fewer misses than the first cold run.
        if tool_misses1 >= 2:
            assert new_misses < tool_misses1, (
                f"Expected second invoke to add fewer misses than first cold run; "
                f"first_total={tool_misses1}, added={new_misses}"
            )
        if new_misses < tool_misses1:
            assert miss_penalty_second < miss_penalty_first, (
                "When second run adds fewer misses, its miss-path CPU time should drop vs first run"
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
