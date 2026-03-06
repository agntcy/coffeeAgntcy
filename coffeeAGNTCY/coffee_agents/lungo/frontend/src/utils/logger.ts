/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * - logger: safe logger; no output in production (all levels no-op).
 * - unsafeLogger: may log in production; use only for non-sensitive diagnostics.
 *   All payloads are passed through a redaction layer before output.
 **/

import { env } from "@/utils/env"

export type LogLevel = "debug" | "info" | "warn" | "error"

/** Keys (case-insensitive) whose values are redacted before logging. */
const SENSITIVE_KEYS = new Set([
  "password",
  "passwd",
  "pwd",
  "secret",
  "token",
  "apikey",
  "api_key",
  "accesstoken",
  "access_token",
  "refreshtoken",
  "refresh_token",
  "authorization",
  "auth",
  "cookie",
  "cookies",
  "session",
  "sessionid",
  "session_id",
  "bearer",
  "set-cookie",
  "x-api-key",
  "x-auth-token",
  "credential",
  "credentials",
  "privatekey",
  "private_key",
  "ssn",
  "social_security",
])

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    Object.getPrototypeOf(value) === Object.prototype
  )
}

/**
 * Recursively redact known sensitive keys in plain objects and arrays.
 * Other values (primitives, Error, etc.) are returned as-is.
 */
function redactSensitiveData(value: unknown): unknown {
  if (value === null || value === undefined) {
    return value
  }
  if (Array.isArray(value)) {
    return value.map(redactSensitiveData)
  }
  if (isPlainObject(value)) {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value)) {
      const keyLower = k.toLowerCase()
      if (
        SENSITIVE_KEYS.has(keyLower) ||
        keyLower.includes("password") ||
        keyLower.includes("secret") ||
        keyLower.includes("token")
      ) {
        out[k] = "[REDACTED]"
      } else {
        out[k] = redactSensitiveData(v)
      }
    }
    return out
  }
  return value
}

class Logger {
  private isDev = env.dev

  protected log(_level: LogLevel, _message: string, _data?: unknown) {
    if (!this.isDev) return
    this.doLog(_level, _message, _data)
  }

  protected doLog(level: LogLevel, message: string, data?: unknown) {
    const prefix = `[${level.toUpperCase()}]`

    switch (level) {
      case "debug":
        console.debug(prefix, message, data)
        break
      case "info":
        console.info(prefix, message, data)
        break
      case "warn":
        console.warn(prefix, message, data)
        break
      case "error":
        console.error(prefix, message, data)
        break
    }
  }

  debug(message: string, data?: unknown) {
    this.log("debug", message, data)
  }

  info(message: string, data?: unknown) {
    this.log("info", message, data)
  }

  warn(message: string, data?: unknown) {
    this.log("warn", message, data)
  }

  error(message: string, data?: unknown) {
    this.log("error", message, data)
  }

  apiError(endpoint: string, error: unknown) {
    this.error(`API Error - ${endpoint}`, {
      error: error instanceof Error ? error.message : error,
      stack: error instanceof Error ? error.stack : undefined,
    })
  }
}

/**
 * Logger that may output in production. Use only for non-sensitive diagnostics.
 * All data is redacted for known sensitive keys before being written to console.
 * ESLint warns on usage; avoid logging PII, full responses, or raw payloads.
 */
class UnsafeLogger extends Logger {
  protected override log(level: LogLevel, message: string, data?: unknown) {
    const redacted = redactSensitiveData(data)
    this.doLog(level, message, redacted)
  }

  debug(message: string, data?: unknown) {
    this.log("debug", message, data)
  }

  info(message: string, data?: unknown) {
    this.log("info", message, data)
  }

  warn(message: string, data?: unknown) {
    this.log("warn", message, data)
  }

  error(message: string, data?: unknown) {
    this.log("error", message, data)
  }

  apiError(endpoint: string, error: unknown) {
    this.log("error", `API Error - ${endpoint}`, {
      error: error instanceof Error ? error.message : error,
      stack: error instanceof Error ? error.stack : undefined,
    })
  }
}

export const logger = new Logger()
export const unsafeLogger = new UnsafeLogger()
