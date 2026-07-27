/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { HttpError } from "./types.ts"
import { stripHtml } from "./stripHtml.ts"

export type ParseHttpErrorOptions = {
  endpointLabel?: string
}

const DEFAULT_MESSAGE = "Sorry, something went wrong. Please try again later."

function formatFastApiDetail(detail: unknown): string | undefined {
  if (typeof detail === "string") {
    return stripHtml(detail)
  }

  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (typeof item === "string") {
        return item
      }
      if (item !== null && typeof item === "object") {
        const obj = item as Record<string, unknown>
        const msg = typeof obj.msg === "string" ? obj.msg : undefined
        const loc = Array.isArray(obj.loc)
          ? obj.loc.filter((segment) => segment !== "body").join(".")
          : undefined
        if (msg && loc) {
          return `${loc}: ${msg}`
        }
        if (msg) {
          return msg
        }
      }
      return String(item)
    })
    return stripHtml(parts.join("; "))
  }

  return undefined
}

function getMessageFromJsonBody(body: unknown): string {
  if (typeof body === "string") {
    return stripHtml(body)
  }

  if (body !== null && typeof body === "object" && !Array.isArray(body)) {
    const obj = body as Record<string, unknown>
    const detail = formatFastApiDetail(obj.detail)
    const msg = typeof obj.message === "string" ? obj.message : undefined
    const title = typeof obj.title === "string" ? obj.title : undefined
    const errors = obj.errors
    const firstError =
      Array.isArray(errors) && errors.length > 0 ? errors[0] : undefined
    const fallback =
      typeof firstError === "string"
        ? firstError
        : firstError !== undefined
          ? String(firstError)
          : undefined

    return stripHtml(detail ?? msg ?? title ?? fallback ?? JSON.stringify(body))
  }

  return "Request failed"
}

function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === "AbortError") {
    return true
  }
  return (
    error !== null &&
    typeof error === "object" &&
    "name" in error &&
    error.name === "AbortError"
  )
}

function isNetworkError(error: unknown): boolean {
  return error instanceof TypeError
}

export function parseHttpError(
  error: unknown,
  options?: ParseHttpErrorOptions,
): HttpError {
  if (error instanceof HttpError) {
    return error
  }

  if (isAbortError(error)) {
    return new HttpError("Request was cancelled.", {
      endpointLabel: options?.endpointLabel,
      cause: error,
    })
  }

  if (isNetworkError(error)) {
    return new HttpError("Network error. Please check your connection.", {
      endpointLabel: options?.endpointLabel,
      cause: error,
    })
  }

  if (error instanceof Error && error.message.trim().length > 0) {
    return new HttpError(stripHtml(error.message), {
      endpointLabel: options?.endpointLabel,
      cause: error,
    })
  }

  return new HttpError(DEFAULT_MESSAGE, {
    endpointLabel: options?.endpointLabel,
    cause: error,
  })
}

export async function parseHttpErrorFromResponse(
  response: Response,
  options?: ParseHttpErrorOptions,
): Promise<HttpError> {
  const status = response.status
  let message = `HTTP ${response.status}: ${response.statusText}`

  try {
    const contentType = response.headers.get("content-type") ?? ""
    const raw = (await response.text()).trim()

    if (!raw) {
      return new HttpError(message, {
        status,
        endpointLabel: options?.endpointLabel,
        cause: response,
      })
    }

    if (contentType.includes("application/json")) {
      try {
        const body: unknown = JSON.parse(raw)
        message = getMessageFromJsonBody(body)
      } catch {
        message = stripHtml(raw)
      }
    } else {
      message = stripHtml(raw)
    }
  } catch {
    // keep default message
  }

  return new HttpError(stripHtml(message), {
    status,
    endpointLabel: options?.endpointLabel,
    cause: response,
  })
}
