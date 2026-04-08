# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Static catalog data and DTO converter for architectural patterns.

The values align with the architectural patterns described in
``docs/TERMINOLOGY.md`` and the supervisors that live under
``agents/supervisors/``.
"""

from __future__ import annotations

from api.agentic_workflows.dtos import Pattern, PatternListResponse

PATTERNS: list[str] = [
    "Supervisor-worker",
    "Group chat",
    "Recruiter",
]


def get_patterns_dto_response(patterns: list[str]) -> PatternListResponse:
    """Build a ``PatternListResponse`` from a list of pattern names."""
    return PatternListResponse(items=[Pattern(name=n) for n in patterns])
