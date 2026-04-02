# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Resolved OpenAPI document for the agentic workflows API is structurally valid."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from openapi_spec_validator import validate
from prance import ResolvingParser

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_OPENAPI_ROOT = _LUNGO_ROOT / "schema" / "openapi" / "openapi.yaml"


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_agentic_workflows_openapi_spec_validates() -> None:
    assert _OPENAPI_ROOT.is_file(), f"missing OpenAPI entry {_OPENAPI_ROOT}"
    # Prance may import ``requests`` (optional HTTP resolution); suppress version skew noise.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        parser = ResolvingParser(str(_OPENAPI_ROOT.resolve()), lazy=True)
        parser.parse()
    validate(parser.specification)
    assert "paths" in parser.specification
    assert len(parser.specification["paths"]) >= 1
