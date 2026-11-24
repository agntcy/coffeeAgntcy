# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Keep SageMaker tracing working with the installed instrumentor.

ioa-observe-sdk 1.1.0 still passes ``enrich_token_usage`` when it constructs
``SageMakerInstrumentor``. opentelemetry-instrumentation-sagemaker 0.60.0
removed that argument, so construction raises ``TypeError``, the instrumentor
is skipped, and every traced agent logs an error during startup. Token counts
now come from the API response, so the flag has nothing left to do.
"""

from __future__ import annotations

import inspect

_PATCH_FLAG = "_ignores_enrich_token_usage"


def accept_removed_sagemaker_enrich_kwarg() -> None:
    """Drop ``enrich_token_usage`` if this SageMaker instrumentor rejects it."""
    try:
        from opentelemetry.instrumentation.sagemaker import SageMakerInstrumentor
    except Exception:  # noqa: BLE001
        return

    init = SageMakerInstrumentor.__init__
    if getattr(init, _PATCH_FLAG, False):
        return
    if "enrich_token_usage" in inspect.signature(init).parameters:
        return

    def __init__(self, *args, **kwargs):
        kwargs.pop("enrich_token_usage", None)
        init(self, *args, **kwargs)

    setattr(__init__, _PATCH_FLAG, True)
    SageMakerInstrumentor.__init__ = __init__
