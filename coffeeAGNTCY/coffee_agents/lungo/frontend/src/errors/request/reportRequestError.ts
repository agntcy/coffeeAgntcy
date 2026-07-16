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

function normalizeRequestError(endpoint: string, error: unknown): HttpError {
  if (isHttpError(error)) {
    return error.endpoint
      ? error
      : new HttpError(error.message, {
          status: error.status,
          endpoint,
          cause: error.cause,
        })
  }

  return parseHttpError(error, { endpoint })
}

function buildLogPayload(
  httpError: HttpError,
  context?: ReportRequestErrorContext,
): Record<string, unknown> {
  const { userMessage, ...rest } = context ?? {}

  return {
    message: httpError.message,
    status: httpError.status,
    endpoint: httpError.endpoint,
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
  endpoint: string,
  error: unknown,
  context?: ReportRequestErrorContext,
): HttpError {
  const httpError = normalizeRequestError(endpoint, error)
  const log = env.dev ? logger : unsafeLogger

  log.error(`API Error - ${endpoint}`, buildLogPayload(httpError, context))

  if (context?.userMessage) {
    reportUiError({
      title: "Request failed",
      message: context.userMessage,
      source: endpoint,
    })
  }

  return httpError
}
