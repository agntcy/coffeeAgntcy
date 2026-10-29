# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Case and configuration selection: explicit fields, prompt reading, defaults."""

import pytest

from agents.supervisors.supply_chain.selection import (
    parse_tag,
    resolve_selection,
    validate_fields,
)
from tests.helpers.supply_chain_fakes import FakeLLM


async def test_explicit_fields_win_and_no_llm_call_is_made():
    llm = FakeLLM()  # any call would raise IndexError
    sel = await resolve_selection(
        "run the explicit case", "infeasible", "l9_hybrid", llm_factory=llm
    )
    assert (sel.case, sel.configuration) == ("infeasible", "l9_hybrid")
    assert sel.sources == {"case": "request", "configuration": "request"}
    assert llm.calls == []


async def test_explicit_field_takes_precedence_over_the_prompt():
    llm = FakeLLM({"case": "explicit", "configuration": "l9_hybrid"})
    sel = await resolve_selection(
        "run the explicit case with L9", "infeasible", llm_factory=llm
    )
    assert sel.case == "infeasible"
    assert sel.configuration == "l9_hybrid"
    assert sel.sources == {"case": "request", "configuration": "prompt"}


async def test_prompt_names_case_and_configuration():
    llm = FakeLLM({"case": "infeasible", "configuration": "l9_hybrid"})
    sel = await resolve_selection("run the infeasible case with L9", llm_factory=llm)
    assert (sel.case, sel.configuration) == ("infeasible", "l9_hybrid")
    assert not sel.defaulted
    assert "infeasible" in llm.prompt_text() and "l9_hybrid" in llm.prompt_text()


async def test_unsure_prompt_defaults_and_says_so():
    llm = FakeLLM({"case": None, "configuration": None})
    sel = await resolve_selection("run something", llm_factory=llm)
    assert (sel.case, sel.configuration) == ("ambiguous", "baseline")
    assert sel.defaulted
    assert sel.describe().count("default") == 2


async def test_one_field_read_one_defaulted():
    llm = FakeLLM({"case": "disruption", "configuration": None})
    sel = await resolve_selection("run the disruption case", llm_factory=llm)
    assert (sel.case, sel.configuration) == ("disruption", "baseline")
    assert sel.sources == {"case": "prompt", "configuration": "default"}
    assert sel.describe() == (
        "Running case disruption with configuration baseline "
        "(default, the prompt did not say)."
    )


async def test_empty_prompt_uses_defaults_without_an_llm_call():
    llm = FakeLLM()
    sel = await resolve_selection("  ", llm_factory=llm)
    assert sel.defaulted and llm.calls == []


async def test_unreadable_prompt_falls_back_to_defaults():
    llm = FakeLLM(lambda _messages: (_ for _ in ()).throw(RuntimeError("model down")))
    sel = await resolve_selection("run the explicit case", llm_factory=llm)
    assert (sel.case, sel.configuration) == ("ambiguous", "baseline")


@pytest.mark.parametrize(
    ("case", "configuration"), [("nope", None), (None, "l9_extreme"), ("explicit", "x")]
)
async def test_unknown_explicit_values_are_rejected(case, configuration):
    with pytest.raises(ValueError, match="unknown"):
        await resolve_selection("p", case, configuration, llm_factory=FakeLLM())
    with pytest.raises(ValueError, match="unknown"):
        validate_fields(case, configuration)


def test_validate_fields_accepts_known_and_missing_values():
    validate_fields(None, None)
    validate_fields("disruption", "l9_full")


# -- the closing tag (design D9, task 4.1c) -------------------------------------------


@pytest.mark.parametrize(
    "tag, expected",
    [
        ("(ambiguous/baseline)", ("ambiguous", "baseline")),
        ("(explicit/L9 hybrid)", ("explicit", "l9_hybrid")),
        ("(infeasible/L9 full)", ("infeasible", "l9_full")),
        ("(disruption/l9_hybrid)", ("disruption", "l9_hybrid")),
        ("(Disruption / L9_FULL)", ("disruption", "l9_full")),
        ("( explicit/ l9-hybrid )", ("explicit", "l9_hybrid")),
        ("(ambiguous/BASELINE).", ("ambiguous", "baseline")),
    ],
)
def test_the_tag_reads_every_spelling_of_the_run_type(tag, expected):
    assert (
        parse_tag(f"I'd like to have a 1,000-tonne coffee shipment {tag}") == expected
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "no tag at all",
        "I'd like a shipment (nonsense/baseline)",
        "I'd like a shipment (ambiguous/turbo)",
        "I'd like a shipment (ambiguous)",
        "(ambiguous/baseline) and then some more words",
        "",
    ],
)
def test_an_unknown_or_misplaced_tag_falls_through(prompt):
    assert parse_tag(prompt) is None


async def test_a_tag_with_both_fields_makes_no_llm_call():
    llm = FakeLLM()  # any call would raise IndexError
    sel = await resolve_selection(
        "I'd like a shipment (infeasible/L9 hybrid)", llm_factory=llm
    )
    assert (sel.case, sel.configuration) == ("infeasible", "l9_hybrid")
    assert sel.sources == {"case": "tag", "configuration": "tag"}
    assert llm.calls == [] and not sel.defaulted


async def test_explicit_fields_win_over_the_tag():
    llm = FakeLLM()
    sel = await resolve_selection(
        "A shipment (infeasible/L9 hybrid)",
        "explicit",
        "baseline",
        llm_factory=llm,
    )
    assert (sel.case, sel.configuration) == ("explicit", "baseline")
    assert sel.sources == {"case": "request", "configuration": "request"}


async def test_one_explicit_field_and_the_tag_for_the_other():
    llm = FakeLLM()
    sel = await resolve_selection(
        "A shipment (infeasible/L9 hybrid)", configuration="baseline", llm_factory=llm
    )
    assert (sel.case, sel.configuration) == ("infeasible", "baseline")
    assert sel.sources == {"case": "tag", "configuration": "request"}
    assert llm.calls == []


async def test_an_unknown_tag_goes_on_to_the_model():
    llm = FakeLLM({"case": "explicit", "configuration": None})
    sel = await resolve_selection("A shipment (nonsense/baseline)", llm_factory=llm)
    assert (sel.case, sel.configuration) == ("explicit", "baseline")
    assert sel.sources == {"case": "prompt", "configuration": "default"}
    assert len(llm.calls) == 1
