# Apply before any test or module import that pulls in a2a (e.g. exchange.agent).
# a2a-sdk imports starlette.status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, which starlette
# exposes via __getattr__ with a DeprecationWarning. Defining the attribute here so it
# exists on the module means a2a's import never triggers __getattr__, so no warning.
import starlette.status  # noqa: E402

starlette.status.HTTP_413_REQUEST_ENTITY_TOO_LARGE = (  # noqa: E402
    starlette.status.HTTP_413_CONTENT_TOO_LARGE
)
