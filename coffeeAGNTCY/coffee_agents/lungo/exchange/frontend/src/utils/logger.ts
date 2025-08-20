/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export type LogLevel = "debug" | "info" | "warn" | "error"

class Logger {
  private isDev = process.env.NODE_ENV === "development"

  private log(level: LogLevel, message: string, data?: unknown) {
    if (!this.isDev && level === "debug") return

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

export const logger = new Logger()
