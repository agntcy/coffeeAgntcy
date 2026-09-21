/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Build GitHub blob URLs for workflow/pattern markdown under
 * api/agentic_workflows/docs/workflows/. Slug rules match
 * api/agentic_workflows/workflow_documentation.py.
 */

import { getWorkflowDocumentationGithubUrl } from "@/urls"

export function openWorkflowDocumentationInNewTab(catalogName: string): void {
  window.open(
    getWorkflowDocumentationGithubUrl(catalogName),
    "_blank",
    "noopener,noreferrer",
  )
}
