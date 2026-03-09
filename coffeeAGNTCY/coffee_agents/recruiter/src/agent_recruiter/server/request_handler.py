# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Custom request handler that extracts agent_records from message metadata."""

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import TaskStatusUpdateEvent
import json
from agent_recruiter.common.logging import get_logger

logger = get_logger(__name__)


class RecruiterRequestHandler(DefaultRequestHandler):
    """Custom handler that extracts agent_records and evaluation_results from message metadata."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("RecruiterRequestHandler initialized")
    
    async def _serialize_event(self, event):
        """Override to extract metadata from messages and add to event JSON."""
        logger.info(f"_serialize_event called for event type: {type(event).__name__}")
        
        # Get the default serialization
        if hasattr(super(), '_serialize_event'):
            event_dict = await super()._serialize_event(event)
        else:
            # Fallback to basic serialization
            if hasattr(event, 'model_dump'):
                event_dict = event.model_dump()
            elif hasattr(event, 'dict'):
                event_dict = event.dict()
            else:
                event_dict = {}
        
        # Extract agent_records and evaluation_results from message metadata if present
        if isinstance(event, TaskStatusUpdateEvent):
            if event.status and event.status.message and event.status.message.metadata:
                metadata = event.status.message.metadata
                logger.info(f"Found message metadata: {list(metadata.keys())}")
                if 'agent_records' in metadata and metadata['agent_records']:
                    event_dict['agent_records'] = metadata['agent_records']
                    logger.info(f"Extracted {len(metadata['agent_records'])} agent_records to event")
                if 'evaluation_results' in metadata and metadata['evaluation_results']:
                    event_dict['evaluation_results'] = metadata['evaluation_results']
                if 'selected_agent' in metadata and metadata['selected_agent']:
                    event_dict['selected_agent'] = metadata['selected_agent']
        
        return event_dict
