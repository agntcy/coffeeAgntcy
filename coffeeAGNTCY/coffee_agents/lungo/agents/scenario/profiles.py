# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Loads the fixed demo scenario shared by the evaluator agents."""

import json
from pathlib import Path

_PROFILES_PATH = Path(__file__).with_name("farm_profiles.json")


def load_farm_profiles() -> dict[str, dict]:
    """Return the farm profiles keyed by farm slug (e.g. "brazil")."""
    with _PROFILES_PATH.open() as f:
        return json.load(f)["farms"]


def farms_mentioned(text: str, profiles: dict[str, dict]) -> list[str]:
    """Return farm slugs named in ``text``, or every farm if none is named."""
    lowered = text.lower()
    named = [slug for slug in profiles if slug in lowered]
    return named or list(profiles)
