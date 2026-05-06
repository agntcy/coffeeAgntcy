# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for merge_event_data (no store validation)."""

from __future__ import annotations

import copy

from schema.types import Data, Event

from common.workflow_instance_store.merge import merge_event_data, merge_topology_delta

NODE_A = "node://550e8400-e29b-41d4-a716-446655440010"
NODE_B = "node://550e8400-e29b-41d4-a716-446655440011"
NODE_Z = "node://550e8400-e29b-41d4-a716-446655440099"
INST = "instance://550e8400-e29b-41d4-a716-446655440003"

_METADATA = {
    "timestamp": "2026-01-01T00:00:00Z",
    "schema_version": "1.0.0",
    "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
    "id": "event://550e8400-e29b-41d4-a716-446655440002",
    "type": "StateProgressUpdate",
    "source": "test",
}


def _evt(data: dict) -> Event:
    return Event.model_validate({"metadata": _METADATA, "data": data})


def _dump(m: Data) -> dict:
    return m.model_dump(mode="python")


def test_first_event_establishes_workflow_and_instance():
    ev = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {"id": INST, "topology": {}},
                    },
                }
            }
        }
    )
    out = merge_event_data(None, ev)
    d = _dump(out)
    assert d["workflows"]["w"]["pattern"] == "p"
    assert d["workflows"]["w"]["instances"][INST]["id"] == INST
    assert d["workflows"]["w"]["instances"][INST]["topology"] == {
        "nodes": [],
        "edges": [],
    }


def test_update_merges_fields_not_full_replace():
    base = merge_event_data(
        None,
        _evt(
            {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            INST: {
                                "id": INST,
                                "topology": {
                                    "nodes": [
                                        {
                                            "id": NODE_A,
                                            "operation": "create",
                                            "type": "t",
                                            "label": "L1",
                                            "size": {"width": 1, "height": 1},
                                            "layer_index": 0,
                                        }
                                    ],
                                    "edges": [],
                                },
                            }
                        },
                    }
                }
            }
        ),
    )
    ev2 = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [
                                    {
                                        "id": NODE_A,
                                        "operation": "update",
                                        "label": "L2",
                                    }
                                ],
                            },
                        }
                    },
                }
            }
        }
    )
    out = merge_event_data(base, ev2)
    node = {
        n["id"]: n for n in _dump(out)["workflows"]["w"]["instances"][INST]["topology"]["nodes"]
    }[NODE_A]
    assert node["label"] == "L2"
    assert node["type"] == "t"


def test_read_does_not_overwrite_existing_node():
    ev1 = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [
                                    {
                                        "id": NODE_A,
                                        "operation": "create",
                                        "type": "t1",
                                        "label": "a",
                                        "size": {"width": 1, "height": 1},
                                        "layer_index": 0,
                                    }
                                ],
                            },
                        }
                    },
                }
            }
        }
    )
    out1 = merge_event_data(None, ev1)
    ev2 = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [
                                    {
                                        "id": NODE_A,
                                        "operation": "read",
                                        "type": "t2",
                                        "label": "b",
                                        "size": {"width": 2, "height": 2},
                                        "layer_index": 1,
                                    }
                                ],
                            },
                        }
                    },
                }
            }
        }
    )
    out2 = merge_event_data(out1, ev2)
    node = {
        n["id"]: n for n in _dump(out2)["workflows"]["w"]["instances"][INST]["topology"]["nodes"]
    }[NODE_A]
    assert node["type"] == "t1"
    assert node["label"] == "a"


def test_read_creates_node_when_absent():
    base = merge_event_data(
        None,
        _evt(
            {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            INST: {"id": INST, "topology": {"nodes": [], "edges": []}},
                        },
                    }
                }
            }
        ),
    )
    ev = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [
                                    {
                                        "id": NODE_A,
                                        "operation": "read",
                                        "type": "t",
                                        "label": "from_read",
                                        "size": {"width": 1, "height": 1},
                                        "layer_index": 0,
                                    }
                                ],
                            },
                        }
                    },
                }
            }
        }
    )
    out = merge_event_data(base, ev)
    nodes = _dump(out)["workflows"]["w"]["instances"][INST]["topology"]["nodes"]
    assert len(nodes) == 1
    assert nodes[0]["label"] == "from_read"


def test_topology_nodes_preserve_insertion_order_not_sorted_ids():
    """Lexicographic id order would put NODE_A before NODE_Z; list follows create order."""
    ev = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [
                                    {
                                        "id": NODE_Z,
                                        "operation": "create",
                                        "type": "t",
                                        "label": "z_first",
                                        "size": {"width": 1, "height": 1},
                                        "layer_index": 0,
                                    },
                                    {
                                        "id": NODE_A,
                                        "operation": "create",
                                        "type": "t",
                                        "label": "a_second",
                                        "size": {"width": 1, "height": 1},
                                        "layer_index": 0,
                                    },
                                ],
                                "edges": [],
                            },
                        }
                    },
                }
            }
        }
    )
    out = merge_event_data(None, ev)
    ids = [
        n["id"]
        for n in _dump(out)["workflows"]["w"]["instances"][INST]["topology"]["nodes"]
    ]
    assert ids == [NODE_Z, NODE_A]


def test_delete_idempotent():
    base = merge_event_data(
        None,
        _evt(
            {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            INST: {
                                "id": INST,
                                "topology": {
                                    "nodes": [
                                        {
                                            "id": NODE_A,
                                            "operation": "create",
                                            "type": "t",
                                            "label": "a",
                                            "size": {"width": 1, "height": 1},
                                            "layer_index": 0,
                                        }
                                    ],
                                },
                            }
                        },
                    }
                }
            }
        ),
    )
    del_ev = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [{"id": NODE_A, "operation": "delete"}],
                            },
                        }
                    },
                }
            }
        }
    )
    out1 = merge_event_data(base, del_ev)
    assert _dump(out1)["workflows"]["w"]["instances"][INST]["topology"]["nodes"] == []
    out2 = merge_event_data(out1, del_ev)
    assert _dump(out2)["workflows"]["w"]["instances"][INST]["topology"]["nodes"] == []


def test_update_missing_node_is_noop():
    base = merge_event_data(
        None,
        _evt(
            {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            INST: {"id": INST, "topology": {"nodes": [], "edges": []}},
                        },
                    }
                }
            }
        ),
    )
    ev = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [
                                    {
                                        "id": NODE_A,
                                        "operation": "update",
                                        "label": "ghost",
                                    }
                                ],
                            },
                        }
                    },
                }
            }
        }
    )
    out = merge_event_data(base, ev)
    assert _dump(out)["workflows"]["w"]["instances"][INST]["topology"]["nodes"] == []


def test_two_workflow_keys_coexist():
    ev = _evt(
        {
            "workflows": {
                "w1": {
                    "pattern": "p1",
                    "use_case": "u1",
                    "name": "n1",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {"id": INST, "topology": {}},
                    },
                },
                "w2": {
                    "pattern": "p2",
                    "use_case": "u2",
                    "name": "n2",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {"id": INST, "topology": {}},
                    },
                },
            }
        }
    )
    out = merge_event_data(None, ev)
    assert set(_dump(out)["workflows"].keys()) == {"w1", "w2"}


def test_starting_topology_preserved_when_followup_omits():
    ev1 = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {
                        "nodes": [
                            {
                                "id": NODE_A,
                                "operation": "read",
                                "type": "t",
                                "label": "a",
                                "size": {"width": 1, "height": 1},
                                "layer_index": 0,
                            }
                        ],
                        "edges": [],
                    },
                    "instances": {
                        INST: {"id": INST, "topology": {}},
                    },
                }
            }
        }
    )
    base = merge_event_data(None, ev1)
    ev2 = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {"id": INST, "topology": {}},
                    },
                }
            }
        }
    )
    out = merge_event_data(base, ev2)
    assert len(_dump(out)["workflows"]["w"]["starting_topology"]["nodes"]) == 1


def test_node_delete_leaves_dangling_edge():
    base = merge_event_data(
        None,
        _evt(
            {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            INST: {
                                "id": INST,
                                "topology": {
                                    "nodes": [
                                        {
                                            "id": NODE_A,
                                            "operation": "create",
                                            "type": "t",
                                            "label": "a",
                                            "size": {"width": 1, "height": 1},
                                            "layer_index": 0,
                                        },
                                        {
                                            "id": NODE_B,
                                            "operation": "create",
                                            "type": "t",
                                            "label": "b",
                                            "size": {"width": 1, "height": 1},
                                            "layer_index": 0,
                                        },
                                    ],
                                    "edges": [
                                        {
                                            "id": "edge://550e8400-e29b-41d4-a716-446655440099",
                                            "operation": "create",
                                            "type": "default",
                                            "source": NODE_A,
                                            "target": NODE_B,
                                            "bidirectional": False,
                                            "weight": 1.0,
                                        }
                                    ],
                                },
                            }
                        },
                    }
                }
            }
        ),
    )
    ev = _evt(
        {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [{"id": NODE_A, "operation": "delete"}],
                            },
                        }
                    },
                }
            }
        }
    )
    out = merge_event_data(base, ev)
    topo = _dump(out)["workflows"]["w"]["instances"][INST]["topology"]
    assert NODE_B in {n["id"] for n in topo["nodes"]}
    assert len(topo["edges"]) == 1


def test_merge_topology_delta_same_existing_twice_no_mutation_of_nested():
    """Caller-owned nested dicts under existing_topology must survive merges (pure buckets)."""
    nested = {"outer": {"inner": 1}}
    existing = {
        "nodes": [
            {
                "id": NODE_A,
                "operation": "create",
                "type": "t",
                "label": "L",
                "size": {"width": 1.0, "height": 1.0},
                "layer_index": 0.0,
                "meta": nested,
            }
        ],
        "edges": [],
    }
    nested_before = copy.deepcopy(nested)
    delta = {
        "nodes": [
            {
                "id": NODE_A,
                "operation": "update",
                "meta": {"outer": {"inner": 2}},
            }
        ]
    }
    r1 = merge_topology_delta(existing, delta)
    assert nested == nested_before
    r2 = merge_topology_delta(existing, delta)
    assert nested == nested_before
    assert r1 == r2
    node1 = next(n for n in r1["nodes"] if n["id"] == NODE_A)
    assert node1["meta"]["outer"]["inner"] == 2


def test_merge_only_empty_workflows_and_extra_data():
    ev = _evt({"workflows": {}, "app_state": {"counter": 1}})
    out = merge_event_data(None, ev)
    d = _dump(out)
    assert d["workflows"] == {}
    assert d["app_state"] == {"counter": 1}


def test_merge_empty_workflows_preserves_existing_workflows_and_merges_extra():
    base = merge_event_data(
        None,
        _evt(
            {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {INST: {"id": INST, "topology": {}}},
                    }
                }
            }
        ),
    )
    ev2 = _evt({"workflows": {}, "app_state": {"level": 2}})
    out = merge_event_data(base, ev2)
    d = _dump(out)
    assert "w" in d["workflows"]
    assert d["workflows"]["w"]["pattern"] == "p"
    assert d["app_state"] == {"level": 2}
