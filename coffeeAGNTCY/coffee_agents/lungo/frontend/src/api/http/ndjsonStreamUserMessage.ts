/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { HttpError, isHttpError } from "./types.ts"

export type NdjsonStreamUserMessageVariant = "default" | "short"

/**
 * User-facing copy for NDJSON stream failures (4xx shows server detail; 5xx/network generic).
 */
export function ndjsonStreamUserMessage(
  error: unknown,
  variant: NdjsonStreamUserMessageVariant = "default",
): string {
  if (isHttpError(error)) {
    if (
      error.status !== undefined &&
      error.status >= 400 &&
      error.status < 500
    ) {
      return `HTTP ${error.status} - ${error.message}`
    }
  }

  return variant === "short"
    ? "Sorry, something went wrong. Please try again."
    : "Sorry, something went wrong. Please try again later."
}

export function asHttpError(error: unknown, endpointLabel: string): HttpError {
  if (error instanceof HttpError) {
    return error.endpointLabel
      ? error
      : new HttpError(error.message, {
          status: error.status,
          endpointLabel,
          cause: error.cause,
        })
  }

  if (error instanceof Error) {
    return new HttpError(error.message, { endpointLabel, cause: error })
  }

  return new HttpError(String(error), { endpointLabel, cause: error })
}
