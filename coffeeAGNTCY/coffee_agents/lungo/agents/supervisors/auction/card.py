# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
  AgentCapabilities,
  AgentCard,
  AgentSkill
)

# Auction Supervisor Agent
AUCTION_SUPERVISOR_SKILL = AgentSkill(
  id="get_auction_status",
  name="Get Auction Status",
  description="Returns the current status and results of coffee auctions.",
  tags=["coffee", "auction"],
  examples=[
    "What is the status of the latest coffee auction?",
    "Show me the winning bids for today's auction.",
    "How many lots were sold in the last auction?",
    "Who won the Brazil farm coffee auction?"
  ]
)

AUCTION_SUPERVISOR_CARD = AgentCard(
  name='Auction Supervisor agent',
  id='auction-supervisor-agent',
  description='An AI agent that supervises and reports on coffee auctions.',
  url='',
  version='1.0.0',
  defaultInputModes=["text"],
  defaultOutputModes=["text"],
  capabilities=AgentCapabilities(streaming=True),
  skills=[AUCTION_SUPERVISOR_SKILL],
  supportsAuthenticatedExtendedCard=False,
)