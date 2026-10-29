# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Live probe of one Supply Chain Commitment case against the real model (task 4.3b).

It answers one question before the L9 bridge is built: does the case fail
silently without ACCORD and CONCORD, and how often? It runs the case several
times, with the real language model, and counts the verdicts.

What runs for real: a SLIM server (you start it), the four supplier and
logistics servers as separate processes, the SDK transport, the moderator,
the baseline strategy, the checker, and the model configured in ``.env``.
Every run directory is kept under ``runs/supply_chain/``. L9 is switched off
for every process (``SUPPLY_CHAIN_L9_ENABLED=false``), so the runs show that
the skills are not needed to produce the result.

This sends the negotiation to the configured model: about 20 to 40 calls a
run. Credentials come from ``.env`` and are never printed.

Usage, from ``coffeeAGNTCY/coffee_agents/lungo``::

    docker run -d --name scc-slim-probe -p 56357:46357 \\
      -v "$PWD/config/docker/slim/server-config.yaml:/config.yaml" \\
      ghcr.io/agntcy/slim:2.2.0 /slim --config /config.yaml
    SLIM_SERVER=localhost:56357 .venv/bin/python tests/integration/supply_chain_probe.py \\
      --case ambiguous --runs 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import supply_chain_slim_check as harness  # noqa: E402  (shared child-process helpers)

LUNGO_ROOT = harness.LUNGO_ROOT
sys.path.insert(0, str(LUNGO_ROOT))

SERVER_FILES = {
    "supplier_a": "agents/supply_chain/supplier/server.py",
    "supplier_b": "agents/supply_chain/supplier/server.py",
    "supplier_c": "agents/supply_chain/supplier/server.py",
    "logistics": "agents/supply_chain/logistics/server.py",
}


def start_agents(log_dir: Path, secret: str) -> list[subprocess.Popen]:
    procs = []
    for i, party in enumerate(harness.AGENTS):
        env = harness._child_env(log_dir, secret)
        env["SUPPLY_CHAIN_L9_ENABLED"] = "false"
        env["AGENT_PORT"] = str(harness.FIRST_PORT + i)
        if party != "logistics":
            env["SUPPLIER_ID"] = party.removeprefix("supplier_")
        out = (log_dir / f"{party}.out").open("w")
        procs.append(
            subprocess.Popen(
                [sys.executable, SERVER_FILES[party]],
                cwd=LUNGO_ROOT,
                env=env,
                stdout=out,
                stderr=subprocess.STDOUT,
            )
        )
    return procs


def _clip(text: str, n: int = 260) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "..."


async def one_run(
    runner, case: str, configuration: str, index: int, total: int
) -> dict:
    run_id = None
    record = verdict = None
    async for event in runner.stream(
        f"probe run {index}", case=case, configuration=configuration
    ):
        if event["type"] == "status" and event.get("state") == "started":
            run_id = event["run_id"]
            print(f"[{index}/{total}] {run_id} started", flush=True)
        elif event["type"] == "status" and event.get("state") == "round":
            print(f"        round {event['round']}", flush=True)
        elif event["type"] == "record":
            record = event["record"]
        elif event["type"] == "verdict":
            verdict = event["verdict"]
    run_dir = runner._run_root / run_id
    outcome = json.loads((run_dir / "outcome.json").read_text())
    messages = [
        json.loads(line)
        for line in (run_dir / "messages.jsonl").read_text().splitlines()
    ]
    signals = outcome.get("signals", {})
    return {
        "run_id": run_id,
        "status": record["status"],
        "reason": record["reason"],
        "verdict": verdict["verdict"],
        "codes": verdict["codes"],
        "silent": verdict["silent"],
        "rounds": signals.get("rounds"),
        "plans_proposed": signals.get("plans_proposed"),
        "rejected_replies": signals.get("rejected_replies"),
        "milestone": record.get("milestone"),
        "milestone_definition": record.get("milestone_definition"),
        "options": {lot["supplier"]: lot["transport_option"] for lot in record["lots"]},
        "confirmations": [
            {
                "party": c["party"],
                "version": c["plan_version"],
                "decision": c["decision"],
                "reason": _clip(c["reason"]),
            }
            for c in record["confirmations"]
        ],
        "detail": _clip(outcome.get("detail", "")),
        "messages": len(messages),
        "delivery_mentions": {
            party: sum(
                "deliver" in m["body"].lower()
                for m in messages
                if m["from"] == party and m["kind"] == "negotiation"
            )
            for party in (
                "buyer",
                "supplier_a",
                "supplier_b",
                "supplier_c",
                "logistics",
            )
        },
        "run_dir": str(run_dir),
    }


def classify(result: dict) -> str:
    if result["verdict"] == "INVALID":
        return "invalid"
    if result["verdict"] == "PASS":
        return "pass"
    return "silent_failure" if result["silent"] else "other_failure"


async def probe(case: str, configuration: str, runs: int, secret: str) -> list[dict]:
    os.environ.update(
        SLIM_SERVER=harness.SLIM_SERVER,
        SLIM_SHARED_SECRET=secret,
        OTEL_SDK_DISABLED="true",
        EMIT_WORKFLOW_EVENTS="false",
        SUPPLY_CHAIN_L9_ENABLED="false",
    )
    from agents.supervisors.supply_chain.card import BUYER_CARD
    from agents.supervisors.supply_chain.runner import SupplyChainRunner
    from agents.supervisors.supply_chain.shared import a2a_client_factory
    from agents.supervisors.supply_chain.transport import SlimGroupTransport
    from agents.supply_chain.logistics.card import AGENT_CARD as LOGISTICS_CARD
    from agents.supply_chain.supplier.card import AGENT_CARDS
    from common.a2a_event_middleware import EventEmittingInterceptor
    from config.config import LLM_MODEL

    transport = SlimGroupTransport(
        a2a_client_factory,
        {"logistics": LOGISTICS_CARD, **AGENT_CARDS},
        interceptors=[EventEmittingInterceptor(caller_card=BUYER_CARD)],
    )
    runner = SupplyChainRunner(transport, model=LLM_MODEL)
    print(f"model: {LLM_MODEL}; L9 available: {runner.l9_enabled}", flush=True)

    results = []
    for index in range(1, runs + 1):
        try:
            results.append(await one_run(runner, case, configuration, index, runs))
        except Exception as e:  # keep counting; one broken run must not hide the rest
            print(f"[{index}/{runs}] run raised {type(e).__name__}: {e}", flush=True)
            results.append(
                {
                    "run_id": None,
                    "verdict": "INVALID",
                    "silent": False,
                    "status": "error",
                    "reason": f"{type(e).__name__}: {e}",
                }
            )
        r = results[-1]
        print(
            f"[{index}/{runs}] {classify(r)}: {r['status']}/{r['reason']}, "
            f"verdict {r['verdict']} {r.get('codes', [])}, rounds {r.get('rounds')}, "
            f"rejected {r.get('rejected_replies')}",
            flush=True,
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="ambiguous")
    parser.add_argument("--configuration", default="baseline")
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    secret = secrets.token_urlsafe(32)
    with tempfile.TemporaryDirectory(prefix="scc-probe-") as tmp:
        log_dir = Path(tmp)
        procs = start_agents(log_dir, secret)
        try:
            harness._wait_ready(log_dir, procs, timeout=120)
            print(f"agents ready; SLIM at {harness.SLIM_SERVER}", flush=True)
            results = asyncio.run(
                probe(args.case, args.configuration, args.runs, secret)
            )
        finally:
            for proc in procs:
                proc.terminate()
            for proc in procs:
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()

    counts = Counter(classify(r) for r in results)
    summary = {
        "case": args.case,
        "configuration": args.configuration,
        "runs": len(results),
        "counts": {
            k: counts.get(k, 0)
            for k in ("silent_failure", "other_failure", "pass", "invalid")
        },
        "results": results,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    out = (
        LUNGO_ROOT
        / "runs"
        / "supply_chain"
        / (
            f"probe-{args.case}-{args.configuration}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
        )
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("\n== counts ==")
    for key, value in summary["counts"].items():
        print(f"{key:15} {value}")
    print(f"summary: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
