# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Generated from ``schema/jsonschemas/event_v1.json``.

Do not edit by hand: regenerate with the ``jsonschema-to-pydantic-lungo`` skill.

Verifies that ``schema.types.event`` agrees with the JSON Schema layer
(``schema.validation.validate_data_against_schema``) and with the Python-only
constraint in ``schema.json_schema._enforce_workflow_instance_map_key_id_match``
(mirrored on ``Workflow`` as ``_instance_keys_equal_nested_id``).
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import NamedTuple

import pytest
from pydantic import ValidationError
from schema.errors import SchemaValidationError
from schema.json_schema import load_json_instance_file
from schema.types import Event
from schema.validation import validate_data_against_schema

_KNOWN = "event_v1"
_LUNGO_ROOT = Path(__file__).resolve().parents[4]
_EXAMPLES = _LUNGO_ROOT / "schema" / "jsonschemas" / "examples"
_INSTANCE_KEY = "instance://550e8400-e29b-41d4-a716-446655440003"


class EventInputs(NamedTuple):
    example_filename: str
    mutate: Callable[[dict], None] | None = None


class EventOutputs(NamedTuple):
    schema_exc: type[BaseException] | None = None
    model_exc: type[BaseException] | None = None


class EventCase(NamedTuple):
    case_id: str
    inputs: EventInputs
    outputs: EventOutputs


def _mutate_instance_map_key_invalid_pattern(d: dict) -> None:
    wf = d["data"]["workflows"]["recruiter"]
    inst = next(iter(wf["instances"].values()))
    wf["instances"] = {"not-an-instance-id": inst}


_EVENT_CASES: tuple[EventCase, ...] = (
    EventCase(
        case_id="partial_example_round_trip",
        inputs=EventInputs(example_filename="event_v1_partial.json"),
        outputs=EventOutputs(),
    ),
    EventCase(
        case_id="full_example_round_trip",
        inputs=EventInputs(example_filename="event_v1_full.json"),
        outputs=EventOutputs(),
    ),
    EventCase(
        case_id="empty_workflows_example_round_trip",
        inputs=EventInputs(example_filename="event_v1_empty_workflows.json"),
        outputs=EventOutputs(),
    ),
    EventCase(
        case_id="root_extra_property",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: d.update({"extra": 1}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="missing_required_metadata",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: d.pop("metadata"),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="missing_required_data",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: d.pop("data"),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="metadata_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: d["metadata"].update({"id": "not-a-valid-event-id"}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="metadata_correlation_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: d["metadata"]["correlation"].update(
                {"id": "550e8400-e29b-41d4-a716-446655440001"},
            ),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="metadata_type_unknown_member",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: d["metadata"].update({"type": "BrandNewEmitterEvent"}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="node_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: (
                d["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]
            ).update({"id": "node://not-a-uuid"}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="node_stable_agent_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: (
                d["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]
            ).update({"stable_agent_id": "agent://not-a-uuid"}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="node_operation_unknown_member",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: (
                d["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]
            ).update({"operation": "frobnicate"}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="edge_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: (
                d["data"]["workflows"]["recruiter"]["starting_topology"]["edges"][0]
            ).update({"id": "edge://not-a-uuid"}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="node_label2_empty_string",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: (
                d["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]
            ).update({"label2": ""}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="size_extra_property",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: (
                d["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]
            ).update({"size": {"width": 1.0, "height": 1.0, "depth": 1.0}}),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="instance_map_key_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_instance_map_key_invalid_pattern,
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
    EventCase(
        case_id="instances_map_key_mismatch_with_nested_id",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=lambda d: next(iter(d["data"]["workflows"].values())).update(
                instances={
                    "instance://00000000-0000-4000-8000-000000000001": {
                        "id": _INSTANCE_KEY,
                        "topology": {},
                    },
                },
            ),
        ),
        outputs=EventOutputs(
            schema_exc=SchemaValidationError,
            model_exc=ValidationError,
        ),
    ),
)


@pytest.mark.parametrize("case", [pytest.param(c, id=c.case_id) for c in _EVENT_CASES])
def test_event_payload_schema_and_model(case: EventCase) -> None:
    data = load_json_instance_file(_EXAMPLES / case.inputs.example_filename)
    if case.inputs.mutate is not None:
        data = deepcopy(data)
        case.inputs.mutate(data)

    out = case.outputs
    if out.schema_exc is not None:
        assert out.model_exc is not None, "invalid cases must fail both layers"
        with pytest.raises(out.schema_exc):
            validate_data_against_schema(data, _KNOWN)
        with pytest.raises(out.model_exc):
            Event.model_validate(data)
        return

    assert case.inputs.mutate is None, "valid round-trip cases must not carry a mutation"
    assert out.model_exc is None
    validate_data_against_schema(data, _KNOWN)
    event = Event.model_validate(data)
    dumped = event.model_dump(mode="json", exclude_none=True)
    validate_data_against_schema(dumped, _KNOWN)
    Event.model_validate(dumped)
    assert isinstance(dumped["metadata"]["timestamp"], str)
    assert event.metadata.timestamp.tzinfo is not None


def test_optional_label2_round_trips() -> None:
    data = load_json_instance_file(_EXAMPLES / "event_v1_partial.json")
    data = deepcopy(data)
    node = data["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]
    node["label2"] = "Buyer"

    validate_data_against_schema(data, _KNOWN)
    event = Event.model_validate(data)
    dumped = event.model_dump(mode="json", exclude_none=True)
    validate_data_against_schema(dumped, _KNOWN)
    Event.model_validate(dumped)

    dumped_node = (
        dumped["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]
    )
    assert dumped_node["label2"] == "Buyer"
