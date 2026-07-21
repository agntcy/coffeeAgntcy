# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Guard against LLM integration tests missing the ``llm`` marker."""

from __future__ import annotations

import importlib

import pytest


REQUIRED_LLM_CLASSES: tuple[tuple[str, str], ...] = (
    ("tests.integration.test_auction", "TestAuctionFlows"),
    ("tests.integration.test_logistics_supervisor", "TestLogisticsSupervisorFlows"),
)


def _iter_marks(obj: object) -> list[pytest.Mark]:
    raw = getattr(obj, "pytestmark", None)
    if raw is None:
        return []
    if isinstance(raw, pytest.MarkDecorator):
        return [raw.mark]
    if isinstance(raw, pytest.Mark):
        return [raw]
    return list(raw)


def _class_has_llm_marker(cls: type) -> bool:
    return any(mark.name == "llm" for mark in _iter_marks(cls))


@pytest.mark.parametrize(("module_name", "class_name"), REQUIRED_LLM_CLASSES)
def test_llm_integration_classes_are_marked(module_name: str, class_name: str) -> None:
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    assert _class_has_llm_marker(cls), (
        f"{module_name}.{class_name} must be decorated with @pytest.mark.llm"
    )
