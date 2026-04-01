# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Table-driven instance validation for event_v1."""

from pathlib import Path

import pytest

from schema.errors import SchemaValidationError
from schema.json_schema import (
    is_event_type_registered,
    load_json_instance_file,
    validate_json_instance,
)

KNOWN = "event_v1"
_INSTANCE_KEY = "instance://550e8400-e29b-41d4-a716-446655440003"
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
                    _INSTANCE_KEY: {
                        "id": _INSTANCE_KEY,
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
        pytest.param("file_partial", id="file_partial_example"),
        pytest.param("file_full", id="file_full_example"),
        pytest.param("inline", id="inline_minimal"),
    ],
)
def test_event_v1_valid_instances(source: str):
    if source == "file_partial":
        data = load_json_instance_file(_EXAMPLES / "event_v1_partial.json")
    elif source == "file_full":
        data = load_json_instance_file(_EXAMPLES / "event_v1_full.json")
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
                                _INSTANCE_KEY: {
                                    "id": _INSTANCE_KEY,
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
def test_event_v1_invalid_instances(payload, match_substr: str):
    with pytest.raises(SchemaValidationError) as ei:
        validate_json_instance(payload, KNOWN)
    assert match_substr in ei.value.args[0].lower()


def test_instance_map_key_must_match_workflow_instance_id():
    bad = {
        **_VALID_MINIMAL,
        "data": {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        "instance://00000000-0000-4000-8000-000000000001": {
                            "id": _INSTANCE_KEY,
                            "topology": {},
                        }
                    },
                }
            }
        },
    }
    with pytest.raises(SchemaValidationError) as ei:
        validate_json_instance(bad, KNOWN)
    msg = ei.value.args[0].lower()
    assert "map key" in msg or "instances" in msg
    assert "key" in msg


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
