/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { HttpError, isHttpError, parseHttpError } from "@/api/http"
import { reportUiError } from "@/errors/ui/reportUiError"
import { env } from "@/utils/env"
import { logger, unsafeLogger } from "@/utils/logger"

export type ReportRequestErrorContext = Record<string, unknown> & {
  /** User-facing copy for notification dispatch (wired in errors/ui subtask 3). */
  userMessage?: string
}

function normalizeRequestError(
  endpointLabel: string,
  error: unknown,
): HttpError {
  if (isHttpError(error)) {
    return error.endpointLabel
      ? error
      : new HttpError(error.message, {
          status: error.status,
          endpointLabel,
          cause: error.cause,
        })
  }

  return parseHttpError(error, { endpointLabel })
}

function buildLogPayload(
  httpError: HttpError,
  context?: ReportRequestErrorContext,
): Record<string, unknown> {
  const { userMessage, ...rest } = context ?? {}

  return {
    message: httpError.message,
    status: httpError.status,
    endpointLabel: httpError.endpointLabel,
    ...(userMessage !== undefined ? { userMessage } : {}),
    ...rest,
    error: httpError.message,
    stack: httpError.stack,
  }
}

/**
 * Log a failed HTTP request at feature boundaries.
 * Uses `logger` in dev and redacted `unsafeLogger` in production.
 */
export function reportRequestError(
  endpointLabel: string,
  error: unknown,
  context?: ReportRequestErrorContext,
): HttpError {
  const httpError = normalizeRequestError(endpointLabel, error)
  const log = env.dev ? logger : unsafeLogger

  log.error(`API Error - ${endpointLabel}`, buildLogPayload(httpError, context))

  if (context?.userMessage) {
    reportUiError({
      title: "Request failed",
      message: context.userMessage,
      source: endpointLabel,
    })
  }

  return httpError
}
