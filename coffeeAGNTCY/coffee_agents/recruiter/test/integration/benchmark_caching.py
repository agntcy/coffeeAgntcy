# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Caching Performance Benchmark

Generates a reproducible report card showing tool cache performance.

Run with: uv run python test/integration/benchmark_caching.py
"""

import asyncio
import time
from datetime import datetime
from agent_recruiter.recruiter import RecruiterTeam


async def run_benchmark():
    """Run caching benchmark and generate report."""

    print("=" * 70)
    print("TOOL CACHING PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Initialize the recruiter team
    print("Initializing RecruiterTeam...")
    team = RecruiterTeam()

    # Get initial config
    stats = team.get_cache_stats()
    print(f"Cache Mode: {stats['mode']}")
    print(f"Tool Cache Enabled: {stats['tool_cache'] is not None}")
    if stats['tool_cache']:
        print(f"TTL: {stats['tool_cache'].get('ttl', 'N/A')}s")
        print(f"Max Entries: {stats['tool_cache'].get('max_entries', 'N/A')}")
    print()

    # Test message that triggers tool calls
    test_message = "What skills can I search upon the agent registry with?"
    user_id = "benchmark_user"

    results = []

    # Run 3 iterations with different sessions to measure cache performance
    print("-" * 70)
    print("BENCHMARK RUNS")
    print("-" * 70)

    for i in range(3):
        session_id = f"benchmark_session_{i+1}"

        # Clear stats tracking for this run
        stats_before = team.get_cache_stats()
        hits_before = stats_before["tool_cache"]["hits"] if stats_before["tool_cache"] else 0
        misses_before = stats_before["tool_cache"]["misses"] if stats_before["tool_cache"] else 0

        # Time the request
        start = time.perf_counter()
        await team.invoke(test_message, user_id, session_id)
        elapsed = time.perf_counter() - start

        # Get stats after
        stats_after = team.get_cache_stats()
        hits_after = stats_after["tool_cache"]["hits"] if stats_after["tool_cache"] else 0
        misses_after = stats_after["tool_cache"]["misses"] if stats_after["tool_cache"] else 0

        # Calculate delta
        new_hits = hits_after - hits_before
        new_misses = misses_after - misses_before

        results.append({
            "run": i + 1,
            "session": session_id,
            "time": elapsed,
            "cache_hits": new_hits,
            "cache_misses": new_misses,
        })

        print(f"Run {i+1}: {elapsed:.3f}s | Hits: {new_hits} | Misses: {new_misses}")

    print()

    # Generate report card
    print("=" * 70)
    print("REPORT CARD")
    print("=" * 70)
    print()

    # First run is always cache miss (cold cache)
    first_run = results[0]

    # Subsequent runs should have cache hits
    cached_runs = results[1:]

    print(f"{'Metric':<35} {'Value':>15}")
    print("-" * 50)

    # Cold cache performance
    print(f"{'Cold Cache (Run 1):':<35}")
    print(f"  {'Latency':<33} {first_run['time']:>12.3f}s")
    print(f"  {'Cache Misses':<33} {first_run['cache_misses']:>15}")
    print(f"  {'Cache Hits':<33} {first_run['cache_hits']:>15}")
    print()

    # Warm cache performance
    if cached_runs:
        avg_cached_time = sum(r['time'] for r in cached_runs) / len(cached_runs)
        total_hits = sum(r['cache_hits'] for r in cached_runs)
        total_misses = sum(r['cache_misses'] for r in cached_runs)

        print(f"{'Warm Cache (Runs 2-3):':<35}")
        print(f"  {'Avg Latency':<33} {avg_cached_time:>12.3f}s")
        print(f"  {'Total Cache Hits':<33} {total_hits:>15}")
        print(f"  {'Total Cache Misses':<33} {total_misses:>15}")
        print()

        # Performance improvement
        latency_reduction = first_run['time'] - avg_cached_time
        latency_reduction_pct = (latency_reduction / first_run['time']) * 100 if first_run['time'] > 0 else 0
        speedup = first_run['time'] / avg_cached_time if avg_cached_time > 0 else 0

        print(f"{'Performance Improvement:':<35}")
        print(f"  {'Latency Reduction':<33} {latency_reduction:>12.3f}s")
        print(f"  {'Latency Reduction %':<33} {latency_reduction_pct:>12.1f}%")
        print(f"  {'Speedup Factor':<33} {speedup:>12.2f}x")

    print()

    # Final cache stats
    final_stats = team.get_cache_stats()
    if final_stats["tool_cache"]:
        tc = final_stats["tool_cache"]
        print(f"{'Final Cache Statistics:':<35}")
        print(f"  {'Total Hits':<33} {tc['hits']:>15}")
        print(f"  {'Total Misses':<33} {tc['misses']:>15}")
        print(f"  {'Hit Rate':<33} {tc['hit_rate_percent']:>12.1f}%")
        print(f"  {'Cache Size':<33} {tc['cache_size']:>15}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    if cached_runs and latency_reduction_pct > 0:
        print(f"Tool caching reduced latency by {latency_reduction_pct:.1f}% ({latency_reduction:.2f}s)")
        print(f"achieving a {speedup:.2f}x speedup on repeated similar queries.")
        print()
        print("How it works:")
        print("- First request: Tools called, results cached (cache miss)")
        print("- Subsequent requests: Cached results returned (cache hit)")
        print("- Cache key: hash of (tool_name, arguments)")
        print("- Benefits: Reduced LLM API calls, faster response times")
    else:
        print("Caching did not show improvement in this run.")
        print("This may happen if the LLM chose different tool calls each time.")

    print()

    return results


if __name__ == "__main__":
    asyncio.run(run_benchmark())
