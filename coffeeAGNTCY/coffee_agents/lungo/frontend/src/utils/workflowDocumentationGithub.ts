/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Build GitHub blob URLs for workflow/pattern markdown under
 * api/agentic_workflows/docs/workflows/. Slug rules match
 * api/agentic_workflows/workflow_documentation.py.
 */

import { env } from "@/utils/env"

const GITHUB_REPO_BLOB_ROOT = "https://github.com/agntcy/coffeeAgntcy/blob"

const DOCS_WORKFLOWS_PATH =
    "coffeeAGNTCY/coffee_agents/lungo/api/agentic_workflows/docs/workflows"

const DEFAULT_DOCS_BRANCH = "main"

/** Map catalog display name to markdown basename (without `.md`). */
export function workflowNameToDocumentationSlug(name: string): string {
    let s = name.trim().toLowerCase()
    s = s.replace(/[\u2013\u2014\u2212]/g, "_")
    s = s.replace(/ /g, "_")
    s = s.replace(/[()]/g, "_")
    s = s.replace(/_+/g, "_")
    return s.replace(/^_|_$/g, "")
}

export function getWorkflowDocumentationGithubUrl(catalogName: string): string {
    const branch =
        env.get("VITE_AGENTIC_WORKFLOWS_DOCS_GITHUB_BRANCH") ?? DEFAULT_DOCS_BRANCH
    const slug = workflowNameToDocumentationSlug(catalogName)
    const branchSegment = encodeURIComponent(branch)
    return `${GITHUB_REPO_BLOB_ROOT}/${branchSegment}/${DOCS_WORKFLOWS_PATH}/${slug}.md`
}

export function openWorkflowDocumentationInNewTab(catalogName: string): void {
    window.open(
        getWorkflowDocumentationGithubUrl(catalogName),
        "_blank",
        "noopener,noreferrer",
    )
}