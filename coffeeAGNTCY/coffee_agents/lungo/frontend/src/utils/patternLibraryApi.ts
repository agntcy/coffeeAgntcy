/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Thin client for the pattern reference library endpoints.
 *
 * `GET /patterns/` serves the full library (implemented and reference-only
 * alike) and `GET /pattern-categories/` its grouping; both are independent of
 * the runnable workflow catalog in `agenticWorkflowsApi.ts`. `Pattern.implemented`
 * is the only link between the two resources.
 */

import { agenticWorkflowsAuthHeaders } from "@/api/agenticWorkflowsClient"
import { fetchJson, isHttpError } from "@/api/http"
import {
  buildPatternCategoriesRequest,
  buildPatternCategoryDocumentationRequest,
  buildPatternDocumentationRequest,
  buildPatternsRequest,
  LUNGO_FRONTEND_URLS,
} from "@/urls"

/**
 * One entry of the pattern reference library from `GET /patterns/`.
 *
 * `implemented` is true when the workflow catalog backs this pattern with at
 * least one runnable workflow. The library lists both kinds.
 */
export interface Pattern {
  name: string
  pattern_category: string
  implemented: boolean
}

/** OpenAPI `PatternListResponse` for `GET /patterns/`. */
export interface PatternListResponse {
  items: Pattern[]
}

/** OpenAPI `PatternDocumentationResponse`. */
export interface PatternDocumentation {
  slug: string
  name: string
  title: string
  pattern_category: string
  implemented: boolean
  full_markdown: string
}

/** One agentic design pattern category from `GET /pattern-categories/`. */
export interface PatternCategory {
  name: string
}

/** OpenAPI `PatternCategoryListResponse` for `GET /pattern-categories/`. */
export interface PatternCategoryListResponse {
  items: PatternCategory[]
}

/** OpenAPI `PatternCategoryDocumentationResponse`. */
export interface PatternCategoryDocumentation {
  slug: string
  name: string
  title: string | null
  full_markdown: string
}

/** Log label for pattern list requests (matches router mount). */
export const PATTERNS_LOG_PATH =
  LUNGO_FRONTEND_URLS.apiPaths.patterns.endpointLabel

/** Log label for pattern category list requests (matches router mount). */
export const PATTERN_CATEGORIES_LOG_PATH =
  LUNGO_FRONTEND_URLS.apiPaths.patternCategories.endpointLabel

export class PatternDocumentationNotFoundError extends Error {
  constructor(patternName: string) {
    super(`Pattern documentation not found for: ${patternName}`)
    this.name = "PatternDocumentationNotFoundError"
  }
}

export class PatternCategoryDocumentationNotFoundError extends Error {
  constructor(categoryName: string) {
    super(`Pattern category documentation not found for: ${categoryName}`)
    this.name = "PatternCategoryDocumentationNotFoundError"
  }
}

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === "string" && value.length > 0

const isPlainObjectRecord = (
  value: unknown,
): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value)

const isAbsentOrNonEmptyString = (value: unknown): boolean =>
  value === null || value === undefined || isNonEmptyString(value)

/** Markdown body below the leading H1 (for compact sidebar rendering). */
export const patternCategoryBodyMarkdown = (fullMarkdown: string): string => {
  const lines = fullMarkdown.split("\n")
  if (lines[0]?.startsWith("# ")) {
    return lines.slice(1).join("\n").trim()
  }
  return fullMarkdown.trim()
}

/**
 * Fetch the pattern reference library from `GET /patterns/`.
 *
 * Rows that do not match the expected shape are skipped so one bad entry cannot
 * break the sidebar, mirroring `fetchWorkflowSummaries`.
 */
export const fetchPatterns = async (
  signal?: AbortSignal,
): Promise<Pattern[]> => {
  const request = buildPatternsRequest()
  const body = await fetchJson<PatternListResponse>(request.url, {
    signal,
    endpointLabel: request.endpointLabel,
    headers: agenticWorkflowsAuthHeaders(),
  })
  if (!body || !Array.isArray(body.items)) {
    throw new Error("Failed to fetch patterns: unexpected response shape")
  }
  return body.items.filter(
    (item): item is Pattern =>
      isPlainObjectRecord(item) &&
      isNonEmptyString(item.name) &&
      isNonEmptyString(item.pattern_category) &&
      typeof item.implemented === "boolean",
  )
}

const isPatternDocumentation = (
  value: unknown,
): value is Omit<PatternDocumentation, "title"> & { title?: string | null } =>
  isPlainObjectRecord(value) &&
  isNonEmptyString(value.slug) &&
  isNonEmptyString(value.name) &&
  isNonEmptyString(value.pattern_category) &&
  isNonEmptyString(value.full_markdown) &&
  typeof value.implemented === "boolean" &&
  isAbsentOrNonEmptyString(value.title)

export const fetchPatternDocumentation = async (
  patternName: string,
  signal?: AbortSignal,
): Promise<PatternDocumentation> => {
  const request = buildPatternDocumentationRequest(patternName)

  try {
    const body = await fetchJson<unknown>(request.url, {
      signal,
      endpointLabel: request.endpointLabel,
      headers: agenticWorkflowsAuthHeaders(),
    })
    if (!isPatternDocumentation(body)) {
      throw new Error(
        "Failed to fetch pattern documentation: unexpected response shape",
      )
    }
    return {
      slug: body.slug,
      name: body.name,
      title: body.title ?? body.name,
      pattern_category: body.pattern_category,
      implemented: body.implemented,
      full_markdown: body.full_markdown,
    }
  } catch (error) {
    if (isHttpError(error) && error.status === 404) {
      throw new PatternDocumentationNotFoundError(patternName)
    }
    throw error
  }
}

export const fetchPatternCategories = async (
  signal?: AbortSignal,
): Promise<PatternCategory[]> => {
  const request = buildPatternCategoriesRequest()
  const body = await fetchJson<PatternCategoryListResponse>(request.url, {
    signal,
    endpointLabel: request.endpointLabel,
    headers: agenticWorkflowsAuthHeaders(),
  })
  if (!body || !Array.isArray(body.items)) {
    throw new Error(
      "Failed to fetch pattern categories: unexpected response shape",
    )
  }
  return body.items.filter(
    (item): item is PatternCategory =>
      isPlainObjectRecord(item) && isNonEmptyString(item.name),
  )
}

const isPatternCategoryDocumentation = (
  value: unknown,
): value is Omit<PatternCategoryDocumentation, "title"> & {
  title?: string | null
} =>
  isPlainObjectRecord(value) &&
  isNonEmptyString(value.slug) &&
  isNonEmptyString(value.name) &&
  isNonEmptyString(value.full_markdown) &&
  isAbsentOrNonEmptyString(value.title)

export const fetchPatternCategoryDocumentation = async (
  categoryName: string,
  signal?: AbortSignal,
): Promise<PatternCategoryDocumentation> => {
  const request = buildPatternCategoryDocumentationRequest(categoryName)

  try {
    const body = await fetchJson<unknown>(request.url, {
      signal,
      endpointLabel: request.endpointLabel,
      headers: agenticWorkflowsAuthHeaders(),
    })
    if (!isPatternCategoryDocumentation(body)) {
      throw new Error(
        "Failed to fetch pattern category documentation: unexpected response shape",
      )
    }
    return {
      slug: body.slug,
      name: body.name,
      title: body.title ?? null,
      full_markdown: body.full_markdown,
    }
  } catch (error) {
    if (isHttpError(error) && error.status === 404) {
      throw new PatternCategoryDocumentationNotFoundError(categoryName)
    }
    throw error
  }
}
