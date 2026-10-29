# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Which case and configuration a run uses (design D9).

Precedence, highest first: the explicit request fields; the closing tag of
the prompt, ``(<case>/<run type>)``, read by a fixed rule; an LLM that reads
the prompt with structured output; the defaults. The first streamed event
says which of these each field came from.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, get_args

from pydantic import BaseModel

from agents.supply_chain.common.fixtures import CASES, CaseId
from agents.supply_chain.common.record import Configuration

logger = logging.getLogger("lungo.supply_chain.selection")

CONFIGURATIONS: tuple[str, ...] = get_args(Configuration)
# The configurations that need ACCORD and CONCORD (design D12).
L9_CONFIGURATIONS: tuple[str, ...] = ("l9_hybrid", "l9_full")
L9_DISABLED_MESSAGE = (
    "L9 (ACCORD and CONCORD) is disabled in this deployment "
    "(SUPPLY_CHAIN_L9_ENABLED is off), so only the baseline configuration can run."
)
DEFAULT_CASE: CaseId = "ambiguous"
DEFAULT_CONFIGURATION = "baseline"

Source = Literal["request", "tag", "prompt", "default"]

# The closing tag of a suggested prompt: "(ambiguous/baseline)", "(explicit/L9 hybrid)".
# It must be the last thing in the prompt, optionally followed by a full stop.
_TAG_RE = re.compile(r"\(\s*([A-Za-z]+)\s*/\s*([A-Za-z0-9_ \-]+?)\s*\)\s*[.!]?\s*$")

_INSTRUCTIONS = """\
Read a request to run a simulated supply chain negotiation and say which \
scenario case and which configuration it asks for. Leave a field null when \
the request does not say.

Cases:
- ambiguous: the buyer asks for delivery by a date without naming the milestone
- explicit: the buyer names arrival at the warehouse and the deadline date
- infeasible: no expedited transport capacity exists
- disruption: after a commitment, one supplier's ready time moves

Configurations:
- baseline: plain negotiation, no L9 protocol
- l9_hybrid: the L9 protocol (ACCORD then CONCORD) run by the buyer's code
- l9_full: the L9 protocol with agents using the initiator tools themselves"""


class _Extracted(BaseModel):
    case: Literal["ambiguous", "explicit", "infeasible", "disruption"] | None = None
    configuration: Literal["baseline", "l9_hybrid", "l9_full"] | None = None


@dataclass(frozen=True)
class Selection:
    case: CaseId
    configuration: str
    sources: dict[str, Source] = field(default_factory=dict)

    @property
    def defaulted(self) -> bool:
        return "default" in self.sources.values()

    def describe(self) -> str:
        parts = []
        for name, value in (("case", self.case), ("configuration", self.configuration)):
            origin = self.sources.get(name, "default")
            note = " (default, the prompt did not say)" if origin == "default" else ""
            parts.append(f"{name} {value}{note}")
        return "Running " + " with ".join(parts) + "."


def _check(name: str, value: str | None, allowed: tuple[str, ...]) -> None:
    if value is not None and value not in allowed:
        raise ValueError(f"unknown {name} {value!r}; expected one of {list(allowed)}")


def validate_fields(case: str | None, configuration: str | None) -> None:
    """Raise ``ValueError`` for an explicit field that is not a known value."""
    _check("case", case, CASES)
    _check("configuration", configuration, CONFIGURATIONS)


def parse_tag(prompt: str) -> tuple[str, str] | None:
    """The ``(case, configuration)`` named by the prompt's closing tag, or ``None``.

    The tag is read with a fixed rule, not a model, so the same prompt always
    picks the same run. Letter case and the separator inside the run type do
    not matter (``L9 hybrid``, ``l9_hybrid``, ``L9-Hybrid``). A tag that does
    not name a known case and run type is ignored as a whole.
    """
    found = _TAG_RE.search(prompt)
    if found is None:
        return None
    case = found.group(1).lower()
    configuration = re.sub(r"[ \-]+", "_", found.group(2).strip().lower())
    if case not in CASES or configuration not in CONFIGURATIONS:
        return None
    return case, configuration


async def _extract(prompt: str, llm_factory: Callable[..., Any] | None) -> _Extracted:
    from langchain_core.messages import HumanMessage, SystemMessage

    if llm_factory is None:
        from common.llm import get_llm

        llm_factory = get_llm
    structured = llm_factory(streaming=False).with_structured_output(_Extracted)
    result = await structured.ainvoke(
        [SystemMessage(_INSTRUCTIONS), HumanMessage(prompt)]
    )
    return _Extracted.model_validate(result) if isinstance(result, dict) else result


async def resolve_selection(
    prompt: str,
    case: str | None = None,
    configuration: str | None = None,
    *,
    llm_factory: Callable[..., Any] | None = None,
) -> Selection:
    validate_fields(case, configuration)

    tagged = parse_tag(prompt) if (case is None or configuration is None) else None
    tag_case, tag_configuration = tagged if tagged else (None, None)

    extracted = _Extracted()
    still_open = (case or tag_case) is None or (
        configuration or tag_configuration
    ) is None
    if still_open and prompt.strip():
        try:
            extracted = await _extract(prompt, llm_factory)
        except Exception:
            # An unreadable prompt must not stop a run: use the defaults.
            logger.exception("Could not read case/configuration from the prompt")

    sources: dict[str, Source] = {}

    def pick(
        name: str,
        explicit: str | None,
        tag: str | None,
        read: str | None,
        default: str,
    ) -> str:
        if explicit is not None:
            sources[name] = "request"
            return explicit
        if tag is not None:
            sources[name] = "tag"
            return tag
        if read is not None:
            sources[name] = "prompt"
            return read
        sources[name] = "default"
        return default

    return Selection(
        case=pick("case", case, tag_case, extracted.case, DEFAULT_CASE),  # type: ignore[arg-type]
        configuration=pick(
            "configuration",
            configuration,
            tag_configuration,
            extracted.configuration,
            DEFAULT_CONFIGURATION,
        ),
        sources=sources,
    )
