# Apply before any test or module import that pulls in a2a (e.g. agents.supervisors.recruiter).
# a2a-sdk imports starlette.status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, which starlette
# exposes via __getattr__ with a DeprecationWarning. Defining the attribute here so it
# exists on the module means a2a's import never triggers __getattr__, so no warning.
import starlette.status  # noqa: E402

starlette.status.HTTP_413_REQUEST_ENTITY_TOO_LARGE = (  # noqa: E402
    starlette.status.HTTP_413_CONTENT_TOO_LARGE
)


def _close_huggingface_hub_http_session() -> None:
    """Release the hub's process-wide httpx client (avoids shutdown ResourceWarnings).

    Integration tests import ``sentence_transformers`` / ``huggingface_hub``, which
    keeps a shared HTTP session for the whole pytest process unless closed.
    """
    try:
        from huggingface_hub.utils import close_session

        close_session()
    except Exception:
        pass


def _close_final_asyncio_event_loop() -> None:
    """Close the event loop pytest-asyncio installs after the last async test.

    pytest-asyncio's function-scoped ``event_loop`` fixture replaces the closed
    per-test loop with a fresh "clean" one after every test (see
    ``_provide_clean_event_loop`` in ``pytest_asyncio/plugin.py``) so that code
    calling ``asyncio.get_event_loop()`` afterwards doesn't hit a closed loop.
    Nothing ever closes the one installed after the *last* test, so it is
    garbage-collected at interpreter shutdown at a nondeterministic point,
    firing an "unclosed event loop" ResourceWarning attributed to whatever
    test happens to be running when the GC fires. Closing it here removes
    that flaky failure.
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        loop = None
    if loop is not None and not loop.is_closed():
        loop.close()


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    _close_huggingface_hub_http_session()
    _close_final_asyncio_event_loop()
