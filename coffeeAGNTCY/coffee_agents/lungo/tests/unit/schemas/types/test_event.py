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


def _starting_node(d: dict) -> dict:
    return d["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][0]


def _starting_edge(d: dict) -> dict:
    return d["data"]["workflows"]["recruiter"]["starting_topology"]["edges"][0]


def _mutate_root_extra_property(d: dict) -> None:
    d["extra"] = 1


def _mutate_missing_required_metadata(d: dict) -> None:
    d.pop("metadata")


def _mutate_missing_required_data(d: dict) -> None:
    d.pop("data")


def _mutate_metadata_id_invalid_pattern(d: dict) -> None:
    d["metadata"]["id"] = "not-a-valid-event-id"


def _mutate_metadata_correlation_id_invalid_pattern(d: dict) -> None:
    d["metadata"]["correlation"]["id"] = "550e8400-e29b-41d4-a716-446655440001"


def _mutate_metadata_type_unknown_member(d: dict) -> None:
    d["metadata"]["type"] = "BrandNewEmitterEvent"


def _mutate_node_id_invalid_pattern(d: dict) -> None:
    _starting_node(d)["id"] = "node://not-a-uuid"


def _mutate_node_stable_agent_id_invalid_pattern(d: dict) -> None:
    _starting_node(d)["stable_agent_id"] = "agent://not-a-uuid"


def _mutate_node_operation_unknown_member(d: dict) -> None:
    _starting_node(d)["operation"] = "frobnicate"


def _mutate_edge_id_invalid_pattern(d: dict) -> None:
    _starting_edge(d)["id"] = "edge://not-a-uuid"


def _mutate_node_label_subtitle_empty_string(d: dict) -> None:
    _starting_node(d)["label_subtitle"] = ""


def _mutate_size_extra_property(d: dict) -> None:
    _starting_node(d)["size"] = {"width": 1.0, "height": 1.0, "depth": 1.0}


def _mutate_instance_map_key_invalid_pattern(d: dict) -> None:
    wf = d["data"]["workflows"]["recruiter"]
    inst = next(iter(wf["instances"].values()))
    wf["instances"] = {"not-an-instance-id": inst}


def _mutate_mcp_source_stable_agent_id_invalid_pattern(d: dict) -> None:
    edge = d["data"]["workflows"]["Publish Subscribe"]["instances"][_INSTANCE_KEY][
        "topology"
    ]["edges"][0]
    edge["mcp"]["source_stable_agent_id"] = "agent://not-a-uuid"


def _mutate_instances_map_key_mismatch_with_nested_id(d: dict) -> None:
    next(iter(d["data"]["workflows"].values()))["instances"] = {
        "instance://00000000-0000-4000-8000-000000000001": {
            "id": _INSTANCE_KEY,
            "topology": {},
        }
    }


def _mutate_type_agent_without_agent_record_uri(d: dict) -> None:
    node = _starting_node(d)
    node.pop("agent_record_uri", None)
    node.pop("stable_agent_id", None)


def _mutate_type_mcp_without_agent_record_uri(d: dict) -> None:
    node = d["data"]["workflows"]["recruiter"]["starting_topology"]["nodes"][1]
    node.pop("agent_record_uri", None)
    node.pop("stable_agent_id", None)


def _mutate_type_agent_stable_agent_id_only(d: dict) -> None:
    node = _starting_node(d)
    node.pop("agent_record_uri", None)


_INVALID = EventOutputs(
    schema_exc=SchemaValidationError,
    model_exc=ValidationError,
)

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
        case_id="v1_2_0_example_round_trip",
        inputs=EventInputs(example_filename="event_v1_2_0.json"),
        outputs=EventOutputs(),
    ),
    EventCase(
        case_id="v1_2_1_example_round_trip",
        inputs=EventInputs(example_filename="event_v1_1_2_1.json"),
        outputs=EventOutputs(),
    ),
    EventCase(
        case_id="root_extra_property",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_root_extra_property,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="missing_required_metadata",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_missing_required_metadata,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="missing_required_data",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_missing_required_data,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="metadata_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_metadata_id_invalid_pattern,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="metadata_correlation_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_metadata_correlation_id_invalid_pattern,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="metadata_type_unknown_member",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_metadata_type_unknown_member,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="node_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_node_id_invalid_pattern,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="node_stable_agent_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_node_stable_agent_id_invalid_pattern,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="node_operation_unknown_member",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_node_operation_unknown_member,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="edge_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_edge_id_invalid_pattern,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="mcp_source_stable_agent_id_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_2_0.json",
            mutate=_mutate_mcp_source_stable_agent_id_invalid_pattern,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="node_label_subtitle_empty_string",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_node_label_subtitle_empty_string,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="size_extra_property",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_size_extra_property,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="instance_map_key_invalid_pattern",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_instance_map_key_invalid_pattern,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="instances_map_key_mismatch_with_nested_id",
        inputs=EventInputs(
            example_filename="event_v1_partial.json",
            mutate=_mutate_instances_map_key_mismatch_with_nested_id,
        ),
        outputs=_INVALID,
    ),
    EventCase(
        case_id="type_agent_stable_agent_id_only",
        inputs=EventInputs(
            example_filename="event_v1_1_2_1.json",
            mutate=_mutate_type_agent_stable_agent_id_only,
        ),
        outputs=_INVALID,
    ),
)


_PYDANTIC_ONLY_CASES: tuple[EventCase, ...] = (
    EventCase(
        case_id="type_agent_without_agent_record_uri",
        inputs=EventInputs(
            example_filename="event_v1_1_2_1.json",
            mutate=_mutate_type_agent_without_agent_record_uri,
        ),
        outputs=EventOutputs(schema_exc=None, model_exc=ValidationError),
    ),
    EventCase(
        case_id="type_mcp_without_agent_record_uri",
        inputs=EventInputs(
            example_filename="event_v1_1_2_1.json",
            mutate=_mutate_type_mcp_without_agent_record_uri,
        ),
        outputs=EventOutputs(schema_exc=None, model_exc=ValidationError),
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
    node["label_subtitle"] = "Buyer"

    validate_data_against_schema(data, _KNOWN)
    event = Event.model_validate(data)
    dumped = event.model_dump(mode="json", exclude_none=True)
    validate_data_against_schema(dumped, _KNOWN)
    Event.model_validate(dumped)

    dumped_node = dumped["data"]["workflows"]["recruiter"]["starting_topology"][
        "nodes"
    ][0]
    assert dumped_node["label_subtitle"] == "Buyer"


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _PYDANTIC_ONLY_CASES]
)
def test_event_type_first_pydantic_only(case: EventCase) -> None:
    """``type=agent``/``mcp`` without extension stays schema-valid; this repo's Pydantic rejects it."""
    data = load_json_instance_file(_EXAMPLES / case.inputs.example_filename)
    assert case.inputs.mutate is not None
    data = deepcopy(data)
    case.inputs.mutate(data)
    assert case.outputs.schema_exc is None
    assert case.outputs.model_exc is not None
    validate_data_against_schema(data, _KNOWN)
    with pytest.raises(case.outputs.model_exc):
        Event.model_validate(data)
