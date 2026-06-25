import pytest


@pytest.fixture(autouse=True)
def _disable_otel_for_unit_tests(monkeypatch):
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
