/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export const Role = {
  ASSISTANT: "assistant",
  USER: "user",
} as const
export type RoleType = (typeof Role)[keyof typeof Role]

export type ApiErrorInfo = {
  status?: number
  message: string
}

const FALLBACK_MESSAGE = "Request failed"

/**
 * Render one `detail` entry, or nothing when it carries no readable message.
 * Anything unrenderable is dropped rather than stringified, so a payload we did
 * not anticipate cannot surface as `[object Object]` or a bare `null`.
 */
const formatDetailEntry = (entry: unknown): string | undefined => {
  if (typeof entry === "string") {
    return entry.trim() || undefined
  }

  if (!entry || typeof entry !== "object") {
    return undefined
  }

  const { loc, msg } = entry as { loc?: unknown; msg?: unknown }
  if (typeof msg !== "string" || !msg.trim()) {
    return undefined
  }

  const path = Array.isArray(loc)
    ? loc
        .filter(
          (segment) =>
            segment !== "body" &&
            (typeof segment === "string" || typeof segment === "number"),
        )
        .join(".")
    : ""

  return path ? `${path}: ${msg.trim()}` : msg.trim()
}

/**
 * FastAPI reports errors under `detail`: a string for raised HTTPExceptions and a
 * list of `{loc, msg}` entries for request validation failures.
 */
const formatDetail = (detail: unknown): string | undefined => {
  if (typeof detail === "string") {
    return detail.trim() || undefined
  }

  if (!Array.isArray(detail)) {
    return undefined
  }

  const entries = detail
    .map(formatDetailEntry)
    .filter((entry): entry is string => entry !== undefined)

  return entries.length ? entries.join("; ") : undefined
}

export const parseApiError = (error: any): ApiErrorInfo => {
  if (error?.response) {
    const status = error.response.status
    const data = error.response.data

    if (typeof data === "string") {
      return { status, message: data.trim() || FALLBACK_MESSAGE }
    }

    const detail = formatDetail(data?.detail)
    const message = typeof data?.message === "string" ? data.message.trim() : ""

    return { status, message: detail || message || FALLBACK_MESSAGE }
  }

  return {
    message: "Sorry, something went wrong. Please try again later.",
  }
}
