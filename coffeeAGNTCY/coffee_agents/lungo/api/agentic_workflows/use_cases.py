# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Static catalog data and DTO converter for use-cases.

These are hardcoded until catalog contracts stabilize and a persistent
store is introduced.
"""

from __future__ import annotations

from api.agentic_workflows.dtos import UseCase, UseCaseListResponse

USE_CASES: list[str] = [
    "Coffee Agency",
]


def get_use_cases_dto_response(use_cases: list[str]) -> UseCaseListResponse:
    """Build a ``UseCaseListResponse`` from a list of use-case names."""
    return UseCaseListResponse(items=[UseCase(name=n) for n in use_cases])
