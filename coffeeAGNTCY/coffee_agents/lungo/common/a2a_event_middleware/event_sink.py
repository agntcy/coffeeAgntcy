# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Compatibility shim — canonical implementation in ``common.workflow_utils.event_sink``."""

from common.workflow_utils.event_sink import EventSink, WorkflowAPIEventSink

__all__ = ["EventSink", "WorkflowAPIEventSink"]
