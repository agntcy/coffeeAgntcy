/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export type HttpErrorOptions = {
  status?: number
  endpoint?: string
  cause?: unknown
}

export class HttpError extends Error {
  readonly status?: number
  readonly endpoint?: string
  readonly cause?: unknown

  constructor(message: string, options?: HttpErrorOptions) {
    super(message)
    this.name = "HttpError"
    this.status = options?.status
    this.endpoint = options?.endpoint
    this.cause = options?.cause
  }
}

export function isHttpError(error: unknown): error is HttpError {
  return error instanceof HttpError
}
