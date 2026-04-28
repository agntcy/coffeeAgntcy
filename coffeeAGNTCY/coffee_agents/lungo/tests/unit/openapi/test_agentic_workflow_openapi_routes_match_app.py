# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Agentic Workflows OpenAPI path/method set matches the FastAPI router (no extra docs routes)."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from fastapi import FastAPI
from prance import ResolvingParser

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_OPENAPI_ROOT = _LUNGO_ROOT / "schema" / "openapi" / "openapi.yaml"

_HTTP_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "trace"},
)


def _operations_from_paths(paths: object) -> set[tuple[str, str]]:
    """Return {(path, METHOD), ...} for OpenAPI-style path items."""
    out: set[tuple[str, str]] = set()
    if not isinstance(paths, dict):
        return out
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for key, val in item.items():
            k = key.lower()
            if k in _HTTP_METHODS and isinstance(val, dict):
                out.add((str(path), k.upper()))
    return out


def _minimal_agentic_app() -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    return app


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_agentic_workflows_spec_paths_match_fastapi_router() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        parser = ResolvingParser(str(_OPENAPI_ROOT.resolve()), lazy=True)
        parser.parse()
    spec_paths = parser.specification.get("paths")
    spec_ops = _operations_from_paths(spec_paths)

    app = _minimal_agentic_app()
    generated = app.openapi()
    app_ops = _operations_from_paths(generated.get("paths"))

    assert spec_ops == app_ops, (
        f"spec vs app path/method mismatch.\n"
        f"Only in spec: {sorted(spec_ops - app_ops)}\n"
        f"Only in app: {sorted(app_ops - spec_ops)}"
    )
