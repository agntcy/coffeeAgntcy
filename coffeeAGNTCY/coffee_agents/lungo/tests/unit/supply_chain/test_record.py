# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Commitment record model, confirmation counting and schema drift."""

import json

import pytest
from pydantic import ValidationError

from agents.supply_chain.common.record import (
    RECORD_SCHEMA_PATH,
    CommitmentRecord,
    Confirmation,
    record_json_schema,
)


def _record(**kw) -> CommitmentRecord:
    base = dict(
        run_id="r1",
        case="explicit",
        configuration="baseline",
        plan_version=1,
        status="committed",
        reason="buyer_decision",
    )
    base.update(kw)
    return CommitmentRecord(**base)


def test_valid_record_counts_matching_confirmations():
    rec = _record(
        confirmations=[
            Confirmation(party="buyer", plan_version=1, decision="confirm", seq=10),
            Confirmation(party="logistics", plan_version=1, decision="confirm", seq=11),
        ]
    )
    assert set(rec.counted_confirmations()) == {"buyer", "logistics"}
    assert rec.counted_confirmations()["logistics"].seq == 11


def test_missing_required_field_is_rejected():
    with pytest.raises(ValidationError):
        CommitmentRecord(
            run_id="r1", case="explicit", configuration="baseline", status="committed"
        )


def test_unknown_case_or_status_is_rejected():
    with pytest.raises(ValidationError):
        _record(case="other")
    with pytest.raises(ValidationError):
        _record(status="agreed")


def test_other_version_and_rejections_do_not_count():
    rec = _record(
        plan_version=2,
        confirmations=[
            Confirmation(party="supplier_c", plan_version=1, decision="confirm", seq=5),
            Confirmation(party="supplier_b", plan_version=2, decision="reject", seq=20),
            Confirmation(party="buyer", plan_version=2, decision="confirm", seq=21),
        ],
    )
    assert set(rec.counted_confirmations()) == {"buyer"}


def test_schema_file_matches_model():
    on_disk = json.loads(RECORD_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert on_disk == record_json_schema(), (
        "Regenerate with: uv run python -m agents.supply_chain.common.record"
    )
