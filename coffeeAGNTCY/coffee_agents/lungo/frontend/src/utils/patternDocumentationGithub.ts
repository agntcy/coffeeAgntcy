/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Opens the GitHub blob view of a pattern reference document. Slug rules match
 * api/agentic_workflows/pattern_documentation.py.
 */

import { getPatternDocumentationGithubUrl } from "@/urls"

export function openPatternDocumentationInNewTab(patternName: string): void {
  window.open(
    getPatternDocumentationGithubUrl(patternName),
    "_blank",
    "noopener,noreferrer",
  )
}
