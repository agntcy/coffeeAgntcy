"""Shared pytest configuration and fixtures."""

import pytest


pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
