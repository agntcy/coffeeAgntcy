import asyncio

from slim_bindings import (
    Slim,
    PyName,
    PyService,
    PyIdentityProvider,
    PyIdentityVerifier,
)

def shared_secret_identity(
    identity: str, secret: str
) -> tuple[PyIdentityProvider, PyIdentityVerifier]:
    """
    Create a provider and verifier using a shared secret.

    :param identity: A unique string, identifier of the app.
    :param secret: A shared secret used for authentication.
    :return: A tuple of (provider, verifier).
    """
    provider: PyIdentityProvider = PyIdentityProvider.SharedSecret(
        identity=identity, shared_secret=secret
    )
    verifier: PyIdentityVerifier = PyIdentityVerifier.SharedSecret(
        identity=identity, shared_secret=secret
    )

    return provider, verifier


async def create_slim_app(secret: str, local_name: PyName) -> PyService:
    """
    Create a SLIM app instance with the given shared secret.
    This app will be used to communicate with other SLIM nodes in the network.

    :param secret: A shared secret used for authentication.
    :param local_name: A unique name for the SLIM app instance.
                       It will be used to identify the app in the SLIM network.
    :return: A SLIM app instance.
    """

    # Create the provider and verifier using the shared secret.
    provider, verifier = shared_secret_identity(
        identity=f"{local_name}",
        secret=secret,
    )

    # Create the SLIM app. This is a in-process SLIM client that can be used to
    # exchange messages with other SLIM nodes in the network.
    slim_app = await Slim.new(local_name, provider, verifier)

    # Connect the SLIM app to the SLIM network.
    _ = await slim_app.connect(
        {"endpoint": "http://127.0.0.1:46357", "tls": {"insecure": True}}
    )

    # Return the SLIM app instance.
    return slim_app
