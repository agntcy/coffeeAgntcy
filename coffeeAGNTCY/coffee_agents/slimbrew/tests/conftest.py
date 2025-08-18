import os
import pytest_asyncio


from dotenv import load_dotenv

from slim_bindings import (
    PyName
)

@pytest_asyncio.fixture
def slim_endpoint():
    return "http://127.0.0.1:46357"

@pytest_asyncio.fixture
def shared_secret():
    load_dotenv()
    return os.environ.get("SLIM_SHARED_SECRET")

@pytest_asyncio.fixture
def moderator_name():
    return PyName("agntcy", "slimbrew", "moderator")

@pytest_asyncio.fixture
def topic_name():
    return PyName("agntcy", "slimbrew", "groupchat")