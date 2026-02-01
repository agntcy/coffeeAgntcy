# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
A2A protocol record parser.

Parses A2A AgentCard JSON records into AgentEvalConfig for evaluation.
"""

from typing import Union

from a2a.types import AgentCard
from rogue_sdk.types import AuthType, Protocol, Transport

from agent_recruiter.common.logging import get_logger
from agent_recruiter.interviewers.models import AgentEvalConfig

logger = get_logger(__name__)


def parse_a2a_agent_record(raw_json: Union[str, dict]) -> AgentEvalConfig:
    """Parse an A2A agent record into AgentEvalConfig.

    Uses AgentCard.model_validate_json for parsing A2A card data.

    Args:
        raw_json: Either a JSON string or dict containing A2A AgentCard data

    Returns:
        AgentEvalConfig with extracted agent information

    Raises:
        ValueError: If the record cannot be parsed as an AgentCard
    """
    logger.debug("Parsing A2A agent record")

    # Parse using AgentCard.model_validate_json
    try:
        if isinstance(raw_json, str):
            agent_card = AgentCard.model_validate_json(raw_json)
        else:
            agent_card = AgentCard.model_validate(raw_json)
    except Exception as e:
        logger.error(f"Failed to parse A2A AgentCard: {e}")
        raise ValueError(f"Invalid A2A AgentCard: {e}") from e

    logger.info(f"Successfully parsed AgentCard for agent: {agent_card.name}")

    # Extract URL - required field
    if not agent_card.url:
        raise ValueError("AgentCard missing required 'url' field")

    config = AgentEvalConfig(
        protocol=Protocol.A2A,
        transport=Transport.HTTP,
        evaluated_agent_url=agent_card.url,
        auth_type=AuthType.NO_AUTH,
        auth_credentials=None,
        agent_name=agent_card.name,
        agent_description=agent_card.description,
    )

    logger.info(
        f"Parsed A2A agent record",
        extra={
            "agent_name": agent_card.name,
            "url": agent_card.url,
        }
    )

    return config
