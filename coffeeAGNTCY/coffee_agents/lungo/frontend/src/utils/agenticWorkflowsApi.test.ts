/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import {
  fetchWorkflowDocumentation,
  WorkflowDocumentationNotFoundError,
} from "./agenticWorkflowsApi"

const originalFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = originalFetch
  vi.restoreAllMocks()
})

const mockFetch = (status: number, body: unknown) => {
  const fn = vi.fn(
    async () =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
  )
  globalThis.fetch = fn as unknown as typeof fetch
  return fn
}

describe("fetchWorkflowDocumentation", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_AGENTIC_WORKFLOWS_API_URL", "http://test-host:1234")
  })

  it("returns parsed documentation on 200", async () => {
    mockFetch(200, {
      slug: "feedback_loop",
      workflow_name: "Feedback Loop",
      title: "Feedback Loop",
      sections: [],
      full_markdown: "# Feedback Loop\n\nBody.",
    })

    const doc = await fetchWorkflowDocumentation("Feedback Loop")
    expect(doc.workflow_name).toBe("Feedback Loop")
    expect(doc.title).toBe("Feedback Loop")
    expect(doc.full_markdown).toBe("# Feedback Loop\n\nBody.")
  })

  it("URL-encodes the pattern name (spaces become %20)", async () => {
    const fn = mockFetch(200, {
      slug: "feedback_loop",
      workflow_name: "Feedback Loop",
      title: "Feedback Loop",
      sections: [],
      full_markdown: "body",
    })

    await fetchWorkflowDocumentation("Feedback Loop")
    const firstCall = fn.mock.calls[0] as unknown as [string]
    expect(firstCall[0]).toContain(
      "/agentic-workflows/Feedback%20Loop/documentation/",
    )
  })

  it("throws WorkflowDocumentationNotFoundError on 404", async () => {
    mockFetch(404, { detail: "Workflow documentation not found for: MadeUp" })

    await expect(fetchWorkflowDocumentation("MadeUp")).rejects.toBeInstanceOf(
      WorkflowDocumentationNotFoundError,
    )
  })

  it("throws a generic Error (not NotFound) on 401 Unauthorized", async () => {
    mockFetch(401, { detail: "Unauthorized" })

    const err = await fetchWorkflowDocumentation("Anything").catch((e) => e)
    expect(err).toBeInstanceOf(Error)
    expect(err).not.toBeInstanceOf(WorkflowDocumentationNotFoundError)
    expect(String(err)).toMatch(/HTTP 401/)
  })

  it("throws a generic Error on other non-OK responses", async () => {
    mockFetch(500, { detail: "Server error" })

    await expect(fetchWorkflowDocumentation("Anything")).rejects.toThrow(
      /HTTP 500/,
    )
  })

  it("throws on unexpected response shape", async () => {
    mockFetch(200, { unexpected: "shape" })

    await expect(fetchWorkflowDocumentation("Anything")).rejects.toThrow(
      /unexpected response shape/,
    )
  })
})
