# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Start one helper agent: ``python agents/helper/run_agent.py translator``."""

import config.logging_config  # noqa: F401 - runs setup on import; must be first

import asyncio
import importlib
import sys

from agents.helper.base import serve
from dotenv import load_dotenv

AGENTS = ("translator", "translation_checker", "scam_checker", "advisor")

if __name__ == "__main__":
    load_dotenv()
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    if name not in AGENTS:
        sys.exit(f"usage: run_agent.py {{{'|'.join(AGENTS)}}}")
    module = importlib.import_module(f"agents.helper.{name}.agent")
    try:
        asyncio.run(serve(module.CARD, module.handle, getattr(module, "think", None)))
    except KeyboardInterrupt:
        pass
