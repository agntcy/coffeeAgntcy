# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Table-driven instance validation for session_state_progress_v1."""

from pathlib import Path

import pytest

from schema.errors import SchemaValidationError
from schema.json_schema import (
    is_event_type_registered,
    load_json_instance_file,
    validate_json_instance,
)

KNOWN = "session_state_progress_v1"
_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLES = _LUNGO_ROOT / "schema" / "jsonschemas" / "examples"


_VALID_MINIMAL = {
    "metadata": {
        "timestamp": "2026-01-01T00:00:00Z",
        "schema_version": "1.0.0",
        "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
        "id": "event://550e8400-e29b-41d4-a716-446655440002",
        "type": "RecruiterNodeSearch",
        "source": "t",
    },
    "data": {
        "workflows": {
            "w": {
                "pattern": "p",
                "use_case": "u",
                "name": "n",
                "starting_topology": {"nodes": [], "edges": []},
                "instances": {
                    "i": {
                        "id": "instance://550e8400-e29b-41d4-a716-446655440003",
                        "topology": {},
                    }
                },
            }
        }
    },
}


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("file_event", id="file_event_example"),
        pytest.param("file_snapshot", id="file_snapshot_example"),
        pytest.param("inline", id="inline_minimal"),
    ],
)
def test_session_state_progress_v1_valid_instances(source: str):
    if source == "file_event":
        data = load_json_instance_file(_EXAMPLES / "session_state_progress_v1_event.json")
    elif source == "file_snapshot":
        data = load_json_instance_file(_EXAMPLES / "session_state_progress_v1_snapshot.json")
    else:
        data = _VALID_MINIMAL
    validate_json_instance(data, KNOWN)


@pytest.mark.parametrize(
    "payload,match_substr",
    [
        pytest.param(
            {"metadata": _VALID_MINIMAL["metadata"], "data": _VALID_MINIMAL["data"], "extra": 1},
            "additional",
            id="root_extra_property",
        ),
        pytest.param(
            {
                "metadata": {
                    **_VALID_MINIMAL["metadata"],
                    "correlation": {"id": "550e8400-e29b-41d4-a716-446655440001"},
                },
                "data": _VALID_MINIMAL["data"],
            },
            "does not match",
            id="correlation_id_not_prefixed",
        ),
        pytest.param(
            {"metadata": _VALID_MINIMAL["metadata"], "data": {}},
            "workflows",
            id="missing_workflows",
        ),
        pytest.param(
            {
                "metadata": _VALID_MINIMAL["metadata"],
                "data": {
                    "workflows": {
                        "w": {
                            "use_case": "u",
                            "name": "n",
                            "starting_topology": {"nodes": [], "edges": []},
                            "instances": {
                                "i": {
                                    "id": "instance://550e8400-e29b-41d4-a716-446655440003",
                                    "topology": {},
                                }
                            },
                        }
                    }
                },
            },
            "pattern",
            id="workflow_missing_pattern",
        ),
    ],
)
def test_session_state_progress_v1_invalid_instances(payload, match_substr: str):
    with pytest.raises(SchemaValidationError) as ei:
        validate_json_instance(payload, KNOWN)
    assert match_substr in ei.value.args[0].lower()


def test_unknown_metadata_type_fails_validation():
    payload = {
        **_VALID_MINIMAL,
        "metadata": {**_VALID_MINIMAL["metadata"], "type": "BrandNewEmitterEvent"},
    }
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_json_instance(payload, KNOWN)
    msg = exc_info.value.args[0]
    assert "BrandNewEmitterEvent" in msg
    assert is_event_type_registered("BrandNewEmitterEvent") is False
