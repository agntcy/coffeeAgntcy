# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for merge_event_data (no schema validation)."""

from __future__ import annotations

from common.workflow_instance_store.merge import merge_event_data

NODE_A = "node://550e8400-e29b-41d4-a716-446655440010"
NODE_B = "node://550e8400-e29b-41d4-a716-446655440011"
INST = "instance://550e8400-e29b-41d4-a716-446655440003"


def _evt(data: dict) -> dict:
    return {"data": data}


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
    assert out["workflows"]["w"]["pattern"] == "p"
    assert out["workflows"]["w"]["instances"][INST]["id"] == INST
    assert out["workflows"]["w"]["instances"][INST]["topology"] == {
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
    node = {n["id"]: n for n in out["workflows"]["w"]["instances"][INST]["topology"]["nodes"]}[
        NODE_A
    ]
    assert node["label"] == "L2"
    assert node["type"] == "t"


def test_create_and_read_replace_full_node():
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
    node = {n["id"]: n for n in out2["workflows"]["w"]["instances"][INST]["topology"]["nodes"]}[
        NODE_A
    ]
    assert node["type"] == "t2"
    assert node["label"] == "b"


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
    assert out1["workflows"]["w"]["instances"][INST]["topology"]["nodes"] == []
    out2 = merge_event_data(out1, del_ev)
    assert out2["workflows"]["w"]["instances"][INST]["topology"]["nodes"] == []


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
    assert out["workflows"]["w"]["instances"][INST]["topology"]["nodes"] == []


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
    assert set(out["workflows"].keys()) == {"w1", "w2"}


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
                    "instances": {
                        INST: {"id": INST, "topology": {}},
                    },
                }
            }
        }
    )
    out = merge_event_data(base, ev2)
    assert len(out["workflows"]["w"]["starting_topology"]["nodes"]) == 1


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
    assert NODE_B in {n["id"] for n in out["workflows"]["w"]["instances"][INST]["topology"]["nodes"]}
    assert len(out["workflows"]["w"]["instances"][INST]["topology"]["edges"]) == 1

