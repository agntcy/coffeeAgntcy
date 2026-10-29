# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Live check of Supply Chain Commitment step delivery over SLIM (task 4.2b).

It proves the transport decision (design D3): a moderator step addressed to
some agents is delivered to exactly those agents, each addressee replies once,
nobody else produces a message, and the Buyer persona can be called in-process
in the same step.

What runs for real: a SLIM server (you start it), the supplier and logistics
server code (``agents/supply_chain/*/server.py``) as separate processes, the
SDK's ``broadcast_message``, ``SlimGroupTransport`` and ``Moderator``.
What is fake: the language model. Every agent answers with an echo, so the
check costs no LLM calls.

Usage, from ``coffeeAGNTCY/coffee_agents/lungo``::

    docker run -d --name scc-slim-check -p 56357:46357 \\
      -v "$PWD/config/docker/slim/server-config.yaml:/config.yaml" \\
      ghcr.io/agntcy/slim:2.2.0 /slim --config /config.yaml
    SLIM_SERVER=localhost:56357 uv run python tests/integration/supply_chain_slim_check.py

The shared secret is generated for each run and handed to the child processes
through their environment; nothing is stored.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LUNGO_ROOT = Path(__file__).resolve().parents[2]
SLIM_SERVER = os.environ.get("SLIM_SERVER", "localhost:56357")
FIRST_PORT = 19096
AGENTS = ("supplier_a", "supplier_b", "supplier_c", "logistics")
SLOW_MARKER = "SLOWREPLY"
SLOW_SECONDS = 30


def _child_env(log_dir: Path, secret: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "SLIM_SERVER": SLIM_SERVER,
            "SLIM_SHARED_SECRET": secret,
            "OTEL_SDK_DISABLED": "true",
            "EMIT_WORKFLOW_EVENTS": "false",
            "SCC_CHECK_LOG_DIR": str(log_dir),
            "PYTHONPATH": str(LUNGO_ROOT),
        }
    )
    return env


# -- child mode: the real server with an echo model -------------------------------


class EchoLLM:
    """Stands in for the language model: replies with an echo, confirms plans."""

    def __call__(self, **_kwargs):
        return self

    def bind_tools(self, _tools):
        return self

    def with_structured_output(self, _schema):
        from agents.supply_chain.common.member import ConfirmDecision

        class Confirms:
            async def ainvoke(self, _messages):
                return ConfirmDecision(decision="confirm", reason="echo")

        return Confirms()

    async def ainvoke(self, messages):
        from langchain_core.messages import AIMessage

        if SLOW_MARKER in str(messages[-1].content):
            await asyncio.sleep(SLOW_SECONDS)  # a model slower than SLIM's 20 s default
        return AIMessage(f"echo: {str(messages[-1].content)[:40]}")


def _logged(member, log_path: Path):
    """Wrap ``member.handle`` so every request that reaches it is recorded."""
    handle = member.handle

    async def wrapper(request):
        reply = await handle(request)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"seq": request.seq, "kind": request.kind, "reply": reply.kind}
                )
                + "\n"
            )
        return reply

    member.handle = wrapper


def serve(party: str) -> None:
    from agents.supply_chain.common.member import MemberAgent

    if party == "logistics":
        from agents.supply_chain.logistics import server
    else:
        os.environ["SUPPLIER_ID"] = party.removeprefix("supplier_")
        from agents.supply_chain.supplier import server

    member = MemberAgent(party, EchoLLM())
    _logged(member, Path(os.environ["SCC_CHECK_LOG_DIR"]) / f"{party}.jsonl")
    server.agent = member
    asyncio.run(server.main())


# -- parent mode: start the agents, drive the moderator ---------------------------


def _start_agents(log_dir: Path, secret: str) -> list[subprocess.Popen]:
    procs = []
    for i, party in enumerate(AGENTS):
        env = _child_env(log_dir, secret)
        if party != "logistics":
            env["SUPPLIER_ID"] = party.removeprefix("supplier_")
        env["AGENT_PORT"] = str(FIRST_PORT + i)
        out = (log_dir / f"{party}.out").open("w")
        procs.append(
            subprocess.Popen(
                [sys.executable, __file__, "--serve", party],
                cwd=LUNGO_ROOT,
                env=env,
                stdout=out,
                stderr=subprocess.STDOUT,
            )
        )
    return procs


def _wait_ready(log_dir: Path, procs: list[subprocess.Popen], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    pending = set(AGENTS)
    while pending and time.monotonic() < deadline:
        for party, proc in zip(AGENTS, procs):
            if proc.poll() is not None:
                raise SystemExit(
                    f"{party} exited early:\n{_tail(log_dir / f'{party}.out')}"
                )
            if (
                party in pending
                and "Agent ready" in (log_dir / f"{party}.out").read_text()
            ):
                pending.discard(party)
        time.sleep(0.5)
    if pending:
        raise SystemExit(f"not ready in {timeout:g}s: {sorted(pending)}")


def _tail(path: Path, lines: int = 25) -> str:
    return "\n".join(path.read_text().splitlines()[-lines:])


def _handled(log_dir: Path) -> dict[str, int]:
    counts = {}
    for party in AGENTS:
        path = log_dir / f"{party}.jsonl"
        counts[party] = len(path.read_text().splitlines()) if path.exists() else 0
    return counts


async def _checks(log_dir: Path, secret: str) -> list[str]:
    os.environ.update(
        SLIM_SERVER=SLIM_SERVER,
        SLIM_SHARED_SECRET=secret,
        OTEL_SDK_DISABLED="true",
        EMIT_WORKFLOW_EVENTS="false",
    )
    from agents.supervisors.supply_chain.card import BUYER_CARD
    from agents.supervisors.supply_chain.limits import Limits
    from agents.supervisors.supply_chain.moderator import Moderator
    from agents.supervisors.supply_chain.shared import a2a_client_factory
    from agents.supervisors.supply_chain.transport import SlimGroupTransport
    from agents.supply_chain.common.member import MemberAgent
    from agents.supply_chain.logistics.card import AGENT_CARD as LOGISTICS_CARD
    from agents.supply_chain.supplier.card import AGENT_CARDS
    from common.a2a_event_middleware import EventEmittingInterceptor

    cards = {"logistics": LOGISTICS_CARD, **AGENT_CARDS}
    transport = SlimGroupTransport(
        a2a_client_factory,
        cards,
        interceptors=[EventEmittingInterceptor(caller_card=BUYER_CARD)],
    )
    run_dir = log_dir / "run"
    run_dir.mkdir()
    mod = Moderator(
        run_id="slim-check",
        case="explicit",
        configuration="baseline",
        transport=transport,
        buyer=MemberAgent("buyer", EchoLLM()),
        limits=Limits(step_timeout=60),
        run_dir=run_dir,
    )

    failures: list[str] = []
    seen = _handled(log_dir)

    async def step(label, kind, to, expect_remote, **kwargs):
        nonlocal seen
        started = time.monotonic()
        try:
            replies = await mod.step(kind, to, f"check: {label}", **kwargs)
        except Exception as e:  # report every failure, then stop the run
            failures.append(f"{label}: step raised {type(e).__name__}: {e}")
            print(f"FAIL {label}: {type(e).__name__}: {e}")
            return
        took = time.monotonic() - started
        now = _handled(log_dir)
        delta = {p: now[p] - seen[p] for p in AGENTS}
        seen = now
        problems = []
        if list(replies) != list(to):
            problems.append(f"replies from {list(replies)}, wanted {list(to)}")
        for party, reply in replies.items():
            if (
                reply.sender != party
                or reply.reply_to != mod.log[-len(replies) - 1].seq
            ):
                problems.append(f"bad reply envelope from {party}")
        for party in AGENTS:
            want = 1 if party in expect_remote else 0
            if delta[party] != want:
                problems.append(
                    f"{party} handled {delta[party]} requests, wanted {want}"
                )
        status = "FAIL" if problems else "ok  "
        print(f"{status} {label}: {took:.1f}s, delivered {delta}")
        for problem in problems:
            print(f"     - {problem}")
            failures.append(f"{label}: {problem}")

    await step(
        "one addressee (supplier_b)",
        "negotiation",
        ["supplier_b"],
        {"supplier_b"},
        sender="buyer",
    )
    trio = ["supplier_a", "supplier_c", "logistics"]
    await step("three addressees", "negotiation", trio, set(trio), sender="buyer")
    everyone = ["buyer", "supplier_a", "supplier_b", "supplier_c", "logistics"]
    await step(
        "all five, buyer in-process",
        "confirm_request",
        everyone,
        set(AGENTS),
        plan_version=1,
    )
    await step(
        "one addressee again (supplier_b)",
        "negotiation",
        ["supplier_b"],
        {"supplier_b"},
        sender="buyer",
    )
    await step(
        "logistics alone", "negotiation", ["logistics"], {"logistics"}, sender="buyer"
    )
    await step("buyer persona alone", "negotiation", ["buyer"], set())
    for n in range(3):
        await step(
            f"repeat {n + 1} (three addressees)",
            "negotiation",
            trio,
            set(trio),
            sender="buyer",
        )
    # What a baseline run does: each round addresses the agents one by one,
    # then a plan goes to a five-party confirm step.
    for n in range(3):
        for party in AGENTS:
            await step(
                f"round {n + 1}, {party} alone",
                "negotiation",
                [party],
                {party},
                sender="buyer",
            )
        await step(
            f"round {n + 1}, confirm all five",
            "confirm_request",
            everyone,
            set(AGENTS),
            plan_version=n + 1,
        )
    # A model slower than SLIM's 20 s request/reply default (SLIM_REQUEST_TIMEOUT_SECONDS)
    # must still be delivered: the step deadline is Limits.step_timeout. This goes
    # last because the marker would otherwise reach later transcripts.
    pair = ["supplier_c", "logistics"]
    await step(
        f"slow addressee ({SLOW_SECONDS}s), {SLOW_MARKER}",
        "negotiation",
        pair,
        set(pair),
        sender="buyer",
    )
    return failures


def main() -> int:
    secret = secrets.token_urlsafe(32)
    with tempfile.TemporaryDirectory(prefix="scc-slim-check-") as tmp:
        log_dir = Path(tmp)
        procs = _start_agents(log_dir, secret)
        try:
            _wait_ready(log_dir, procs, timeout=90)
            print(f"agents ready; SLIM at {SLIM_SERVER}")
            failures = asyncio.run(_checks(log_dir, secret))
        finally:
            for proc in procs:
                proc.terminate()
            for proc in procs:
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
        if failures:
            print(f"\n{len(failures)} problem(s):")
            for failure in failures:
                print(f"  - {failure}")
            for party in AGENTS:
                print(
                    f"\n--- {party} output (tail) ---\n{_tail(log_dir / f'{party}.out')}"
                )
            return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--serve":
        serve(sys.argv[2])
    else:
        raise SystemExit(main())
