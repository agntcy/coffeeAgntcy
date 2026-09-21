/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { HttpError } from "@/api/http"
import {
  fetchPatternCategories,
  fetchPatternCategoryDocumentation,
  fetchPatternDocumentation,
  fetchPatterns,
  PatternCategoryDocumentationNotFoundError,
  patternCategoryBodyMarkdown,
  PatternDocumentationNotFoundError,
} from "@/utils/patternLibraryApi"

const originalFetch = globalThis.fetch

describe("fetchPatterns", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const stubFetch = (
    body: unknown,
    init: { ok?: boolean; status?: number; statusText?: string } = {},
  ): void => {
    const { ok = true, status = 200, statusText = "OK" } = init
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok,
        status,
        statusText,
        json: async () => body,
      })),
    )
  }

  it("returns implemented and reference-only patterns, skipping invalid rows", async () => {
    stubFetch({
      items: [
        {
          name: "Publish-Subscribe",
          pattern_category: "Communication & Messaging",
          implemented: true,
        },
        {
          name: "Supervisor",
          pattern_category: "Orchestration & Control Flow",
          implemented: false,
        },
        { name: "", pattern_category: "Nope", implemented: false },
        { name: "No Category", implemented: false },
        { name: "No Flag", pattern_category: "Nope" },
      ],
    })

    const patterns = await fetchPatterns()

    expect(patterns).toEqual([
      {
        name: "Publish-Subscribe",
        pattern_category: "Communication & Messaging",
        implemented: true,
      },
      {
        name: "Supervisor",
        pattern_category: "Orchestration & Control Flow",
        implemented: false,
      },
    ])
  })

  it.each([
    {
      caseName: "non-ok response throws",
      body: {},
      init: { ok: false, status: 500, statusText: "Server Error" },
    },
    {
      caseName: "missing items array throws",
      body: {},
      init: {},
    },
    {
      caseName: "non-array items throws",
      body: { items: null },
      init: {},
    },
  ])("$caseName", async ({ body, init }) => {
    stubFetch(body, init)
    await expect(fetchPatterns()).rejects.toThrow()
  })
})

describe("fetchPatternDocumentation", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_AGENTIC_WORKFLOWS_API_URL", "http://test-host:1234")
  })

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

  const docBody = (over: Record<string, unknown> = {}) => ({
    slug: "feedback_loop",
    name: "Feedback Loop",
    title: "Feedback Loop",
    pattern_category: "Orchestration & Control Flow",
    implemented: false,
    full_markdown: "# Feedback Loop\n\nBody.",
    ...over,
  })

  it("returns parsed documentation on 200", async () => {
    mockFetch(200, docBody())

    const doc = await fetchPatternDocumentation("Feedback Loop")
    expect(doc.name).toBe("Feedback Loop")
    expect(doc.title).toBe("Feedback Loop")
    expect(doc.pattern_category).toBe("Orchestration & Control Flow")
    expect(doc.implemented).toBe(false)
    expect(doc.full_markdown).toBe("# Feedback Loop\n\nBody.")
  })

  it("falls back to the pattern name when the title is null", async () => {
    mockFetch(200, docBody({ title: null }))

    const doc = await fetchPatternDocumentation("Feedback Loop")
    expect(doc.title).toBe("Feedback Loop")
  })

  it("URL-encodes the pattern name (spaces become %20)", async () => {
    const fn = mockFetch(200, docBody())

    await fetchPatternDocumentation("Feedback Loop")
    const firstCall = fn.mock.calls[0] as unknown as [string]
    expect(firstCall[0]).toContain("/patterns/Feedback%20Loop/documentation/")
  })

  it("throws PatternDocumentationNotFoundError on 404", async () => {
    mockFetch(404, { detail: "Pattern documentation not found for: MadeUp" })

    await expect(fetchPatternDocumentation("MadeUp")).rejects.toBeInstanceOf(
      PatternDocumentationNotFoundError,
    )
  })

  it("throws HttpError (not NotFound) on 401 Unauthorized", async () => {
    mockFetch(401, { detail: "Unauthorized" })

    const err = await fetchPatternDocumentation("Anything").catch(
      (e: unknown) => e,
    )
    expect(err).toBeInstanceOf(HttpError)
    expect(err).not.toBeInstanceOf(PatternDocumentationNotFoundError)
    expect((err as HttpError).status).toBe(401)
    expect((err as HttpError).message).toBe("Unauthorized")
  })

  it("throws HttpError on other non-OK responses", async () => {
    mockFetch(500, { detail: "Server error" })

    await expect(fetchPatternDocumentation("Anything")).rejects.toMatchObject({
      status: 500,
      message: "Server error",
    })
  })

  it("throws on unexpected response shape", async () => {
    mockFetch(200, { unexpected: "shape" })

    await expect(fetchPatternDocumentation("Anything")).rejects.toThrow(
      /unexpected response shape/,
    )
  })
})
describe("fetchPatternCategories", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const stubFetch = (
    body: unknown,
    init: { ok?: boolean; status?: number; statusText?: string } = {},
  ): void => {
    const { ok = true, status = 200, statusText = "OK" } = init
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok,
        status,
        statusText,
        json: async () => body,
      })),
    )
  }

  it("returns parsed category names and filters invalid items", async () => {
    stubFetch({
      items: [
        { name: "Orchestration & Control Flow" },
        { name: "Multi-Agent Collaboration" },
        { name: "" },
        { name: null },
        {},
      ],
    })

    const categories = await fetchPatternCategories()

    expect(categories).toEqual([
      { name: "Orchestration & Control Flow" },
      { name: "Multi-Agent Collaboration" },
    ])
  })

  it.each([
    {
      caseName: "non-ok response throws",
      body: {},
      init: { ok: false, status: 500, statusText: "Server Error" },
    },
    {
      caseName: "missing items array throws",
      body: {},
      init: {},
    },
    {
      caseName: "non-array items throws",
      body: { items: null },
      init: {},
    },
  ])("$caseName", async ({ body, init }) => {
    stubFetch(body, init)
    await expect(fetchPatternCategories()).rejects.toThrow()
  })
})

describe("fetchPatternCategoryDocumentation", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const stubFetch = (
    body: unknown,
    init: { ok?: boolean; status?: number } = {},
  ): void => {
    const { ok = true, status = 200 } = init
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok,
        status,
        statusText: ok ? "OK" : "Not Found",
        json: async () => body,
      })),
    )
  }

  it("returns parsed category documentation on 200", async () => {
    stubFetch({
      slug: "orchestration_and_control_flow",
      name: "Orchestration & Control Flow",
      title: "Orchestration & Control Flow",
      full_markdown: "# Orchestration & Control Flow\n\nBody.",
    })

    const doc = await fetchPatternCategoryDocumentation(
      "Orchestration & Control Flow",
    )

    expect(doc.slug).toBe("orchestration_and_control_flow")
    expect(doc.full_markdown).toBe("# Orchestration & Control Flow\n\nBody.")
  })

  it("throws PatternCategoryDocumentationNotFoundError on 404", async () => {
    stubFetch({}, { ok: false, status: 404 })

    await expect(
      fetchPatternCategoryDocumentation("Unknown"),
    ).rejects.toBeInstanceOf(PatternCategoryDocumentationNotFoundError)
  })
})

describe("patternCategoryBodyMarkdown", () => {
  it("strips the leading H1 for sidebar display", () => {
    expect(patternCategoryBodyMarkdown("# Title\n\nParagraph.")).toBe(
      "Paragraph.",
    )
  })
})
