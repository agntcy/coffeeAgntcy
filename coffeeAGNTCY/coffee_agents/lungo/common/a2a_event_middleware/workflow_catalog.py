# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Compatibility shim — canonical implementation in ``common.workflow_utils.workflow_catalog``."""

from common.workflow_utils.workflow_catalog import (
	WorkflowMetadata,
	_load_catalog,
	lookup_workflow,
)

__all__ = ["WorkflowMetadata", "lookup_workflow", "_load_catalog"]
