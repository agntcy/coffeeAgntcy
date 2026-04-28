# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Hand-written Pydantic types agree with JSON Schema validation for packaged examples."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Callable, NamedTuple

import pytest
from pydantic import ValidationError
from schema.errors import SchemaValidationError
from schema.json_schema import load_json_instance_file
from schema.types import Event
from schema.validation import validate_data_against_schema

KNOWN = "event_v1"
_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLES = _LUNGO_ROOT / "schema" / "jsonschemas" / "examples"
_INSTANCE_KEY = "instance://550e8400-e29b-41d4-a716-446655440003"


class Inputs(NamedTuple):
    """Payload source file and optional in-place mutation (``None`` for valid round-trip rows)."""

    example_filename: str
    mutate: Callable[[dict], None] | None = None


class Outputs(NamedTuple):
    """If ``schema_exc`` / ``model_exc`` are set, the payload is invalid for both layers."""

    schema_exc: type[BaseException] | None = None
    model_exc: type[BaseException] | None = None


class Case(NamedTuple):
    """``case_id`` is used as the pytest parametrization id."""

    case_id: str
    inputs: Inputs
    outputs: Outputs


def _mutate_root_extra(d: dict) -> None:
    d["extra"] = 1


def _mutate_metadata_id_invalid(d: dict) -> None:
    # topology_node_item allows partial nodes; invalid event id still fails both layers.
    d["metadata"]["id"] = "not-a-valid-event-id"


def _mutate_instances_key_mismatch(d: dict) -> None:
    wf = next(iter(d["data"]["workflows"].values()))
    wf["instances"] = {
        "instance://00000000-0000-4000-8000-000000000001": {
            "id": _INSTANCE_KEY,
            "topology": {},
        }
    }


# Single table: ``case_id`` is the pytest id. Invalid rows set ``schema_exc`` / ``model_exc``.
_CASES: tuple[Case, ...] = (
    Case(
        case_id="partial_example",
        inputs=Inputs(example_filename="event_v1_partial.json"),
        outputs=Outputs(),
    ),
    Case(
        case_id="full_example",
        inputs=Inputs(example_filename="event_v1_full.json"),
        outputs=Outputs(),
    ),
    Case(
        case_id="empty_workflows_example",
        inputs=Inputs(example_filename="event_v1_empty_workflows.json"),
        outputs=Outputs(),
    ),
    Case(
        case_id="root_extra_property",
        inputs=Inputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_root_extra,
        ),
        outputs=Outputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    Case(
        case_id="metadata_id_invalid_pattern",
        inputs=Inputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_metadata_id_invalid,
        ),
        outputs=Outputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    Case(
        case_id="instances_map_key_mismatch",
        inputs=Inputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_instances_key_mismatch,
        ),
        outputs=Outputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
)


@pytest.mark.parametrize("case", [pytest.param(c, id=c.case_id) for c in _CASES])
def test_event_payload_schema_and_model(case: Case) -> None:
    data = load_json_instance_file(_EXAMPLES / case.inputs.example_filename)
    out = case.outputs

    if out.schema_exc is not None:
        assert out.model_exc is not None
        assert case.inputs.mutate is not None
        data = deepcopy(data)
        case.inputs.mutate(data)

        with pytest.raises(out.schema_exc):
            validate_data_against_schema(data, KNOWN)
        with pytest.raises(out.model_exc):
            Event.model_validate(data)
        return

    assert case.inputs.mutate is None
    validate_data_against_schema(data, KNOWN)
    event = Event.model_validate(data)
    dumped = event.model_dump(mode="json", exclude_none=True)
    validate_data_against_schema(dumped, KNOWN)
    Event.model_validate(dumped)

    assert isinstance(dumped["metadata"]["timestamp"], str)
    assert event.metadata.timestamp.tzinfo is not None
