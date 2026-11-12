# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from agent_recruiter.common.logging import configure_logger, get_logger

configure_logger()

import os

import uvicorn
from dotenv import load_dotenv

from agent_recruiter.server.agent_executor import RecruiterAgentExecutor
from agent_recruiter.server.app import build_app
from agent_recruiter.server.card import (
    AGENT_CARD,
    RECRUITER_AGENT_URL,
    check_advertised_url,
)

load_dotenv()

logger = get_logger(__name__)


def _bind_address() -> tuple[str, int]:
    """Host and port the server listens on.

    This is independent of the URL the card advertises (``RECRUITER_AGENT_URL``):
    the server listens on all interfaces by default, while clients need a
    resolvable host name.
    """
    return (
        os.getenv("RECRUITER_BIND_HOST", "0.0.0.0"),
        int(os.getenv("RECRUITER_PORT", "8881")),
    )


async def main():
    """Serve the recruiter agent card and its A2A JSON-RPC endpoint over HTTP."""
    warning = check_advertised_url(RECRUITER_AGENT_URL)
    if warning:
        logger.warning(warning)
    host, port = _bind_address()
    app = build_app(AGENT_CARD, RecruiterAgentExecutor())
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="info"))
    logger.info("RecruiterAgent ready")
    await server.serve()


if __name__ == "__main__":
    import asyncio

    logger.info("Starting RecruiterAgent server...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise SystemExit(1) from e
