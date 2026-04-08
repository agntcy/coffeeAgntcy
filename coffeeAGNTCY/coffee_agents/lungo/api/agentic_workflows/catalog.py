# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Static catalog data for patterns and use-cases.

These are hardcoded until catalog contracts stabilize and a persistent
store is introduced.  The values align with the architectural patterns
described in ``docs/TERMINOLOGY.md`` and the supervisors that live under
``agents/supervisors/``.

The structures use plain Python types so they can be reused outside the
HTTP layer.  Converter functions produce the corresponding Pydantic DTOs
for the API handlers.
"""

from __future__ import annotations

from api.agentic_workflows.dtos import (
    Pattern,
    PatternListResponse,
    UseCase,
    UseCaseListResponse,
)

PATTERNS: list[str] = [
    "Supervisor-worker",
    "Group chat",
    "Recruiter",
]

USE_CASES: list[str] = [
    "Coffee Agency",
]


def get_patterns_dto_response(patterns: list[str]) -> PatternListResponse:
    """Build a ``PatternListResponse`` from a list of pattern names."""
    return PatternListResponse(items=[Pattern(name=n) for n in patterns])


def get_use_cases_dto_response(use_cases: list[str]) -> UseCaseListResponse:
    """Build a ``UseCaseListResponse`` from a list of use-case names."""
    return UseCaseListResponse(items=[UseCase(name=n) for n in use_cases])
