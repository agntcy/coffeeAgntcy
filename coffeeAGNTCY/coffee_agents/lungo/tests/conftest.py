# Apply before any test or module import that pulls in a2a (e.g. agents.supervisors.recruiter).
# a2a-sdk imports starlette.status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, which starlette
# exposes via __getattr__ with a DeprecationWarning. Defining the attribute here so it
# exists on the module means a2a's import never triggers __getattr__, so no warning.
import starlette.status  # noqa: E402

import pytest  # noqa: E402

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


def _close_dangling_event_loop() -> None:
    """Close whatever event loop is currently installed, if it isn't closed.

    pytest-asyncio's function-scoped ``event_loop`` fixture replaces the closed
    per-test loop with a fresh "clean" one after every async test (see
    ``_provide_clean_event_loop`` in ``pytest_asyncio/plugin.py``) so that code
    calling ``asyncio.get_event_loop()`` afterwards doesn't hit a closed loop.
    That placeholder loop is only closed when the *next* test using the
    ``event_loop`` fixture starts. A sync test that calls ``asyncio.run()`` in
    between never touches that fixture, so ``asyncio.run()`` silently
    overwrites the installed-loop pointer with its own loop without closing
    the old one first, abandoning it unclosed. It is then garbage-collected at
    a nondeterministic later point, firing an "unclosed event loop"
    ResourceWarning attributed to whatever test happens to be running when
    the GC fires. Closing it after every test (and again at session end, for
    whatever the last test leaves behind) removes that flaky failure.
    """
    import asyncio
    import warnings

    try:
        # A thread that never installed a loop makes get_event_loop() create one
        # and emit a DeprecationWarning ("There is no current event loop"). We
        # are only checking for a dangling loop, not asking for one, so silence
        # that warning rather than let "error" filtering turn it into a failure.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            loop = asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        loop = None
    if loop is not None and not loop.is_closed():
        loop.close()


@pytest.fixture(autouse=True)
def _close_dangling_event_loop_after_test():
    yield
    _close_dangling_event_loop()


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    _close_huggingface_hub_http_session()
    _close_dangling_event_loop()
