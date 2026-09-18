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

/**
 * FastAPI reports errors under `detail`: a string for raised HTTPExceptions and a
 * list of `{loc, msg}` entries for request validation failures.
 */
const formatDetail = (detail: unknown): string | undefined => {
  if (typeof detail === "string") {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((entry) => {
        if (entry && typeof entry === "object") {
          const { loc, msg } = entry as { loc?: unknown; msg?: unknown }
          if (typeof msg === "string") {
            const path = Array.isArray(loc)
              ? loc.filter((segment) => segment !== "body").join(".")
              : ""
            return path ? `${path}: ${msg}` : msg
          }
        }
        return String(entry)
      })
      .join("; ")
  }

  return undefined
}

export const parseApiError = (error: any): ApiErrorInfo => {
  if (error?.response) {
    const status = error.response.status
    const data = error.response.data

    if (typeof data === "string") {
      return { status, message: data }
    }

    const detail = formatDetail(data?.detail)
    const message = typeof data?.message === "string" ? data.message : undefined

    return { status, message: detail || message || "Request failed" }
  }

  return {
    message: "Sorry, something went wrong. Please try again later.",
  }
}
