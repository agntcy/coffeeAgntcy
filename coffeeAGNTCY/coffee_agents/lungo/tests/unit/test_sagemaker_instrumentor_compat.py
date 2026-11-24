# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""SageMaker tracing still initializes after enrich_token_usage was removed."""

import logging

from config.sagemaker_instrumentor_compat import accept_removed_sagemaker_enrich_kwarg


def test_sagemaker_constructor_accepts_the_removed_kwarg():
    accept_removed_sagemaker_enrich_kwarg()
    from opentelemetry.instrumentation.sagemaker import SageMakerInstrumentor

    SageMakerInstrumentor(enrich_token_usage=True, exception_logger=lambda _exc: None)


def test_observe_sagemaker_init_does_not_log_a_type_error(caplog):
    accept_removed_sagemaker_enrich_kwarg()
    from ioa_observe.sdk.tracing.tracing import init_sagemaker_instrumentor
    from opentelemetry.instrumentation.sagemaker import SageMakerInstrumentor

    with caplog.at_level(logging.ERROR):
        ok = init_sagemaker_instrumentor(True)
    try:
        assert ok is True
        assert "unexpected keyword argument" not in caplog.text
        assert "Error initializing SageMaker instrumentor" not in caplog.text
    finally:
        instrumentor = SageMakerInstrumentor(exception_logger=lambda _exc: None)
        if instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.uninstrument()
