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


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    _close_huggingface_hub_http_session()
