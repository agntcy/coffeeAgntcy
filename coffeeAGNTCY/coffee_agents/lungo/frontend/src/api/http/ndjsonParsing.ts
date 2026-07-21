/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export type NdjsonLineHandler = (parsed: unknown, raw: string) => void | "stop"

export type NdjsonParseErrorHandler = (raw: string, error: unknown) => void

/**
 * Split a buffer on newlines and invoke `onLine` for each non-empty line.
 * Returns the trailing partial line left in the buffer.
 */
export function consumeNdjsonLines(
  buffer: string,
  onLine: NdjsonLineHandler,
  onParseError?: NdjsonParseErrorHandler,
): string {
  const lines = buffer.split("\n")
  const remainder = lines.pop() ?? ""

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    try {
      const parsed = JSON.parse(trimmed) as unknown
      if (onLine(parsed, trimmed) === "stop") {
        return remainder
      }
    } catch (error) {
      onParseError?.(trimmed, error)
    }
  }

  return remainder
}

/**
 * Extract complete `{...}` JSON objects from a buffer (group messaging stream).
 * Returns the trailing partial fragment left in the buffer.
 */
export function consumeJsonObjectsFromBuffer(
  buffer: string,
  onObject: NdjsonLineHandler,
  onParseError?: NdjsonParseErrorHandler,
): string {
  let remaining = buffer

  while (remaining.length > 0) {
    let braceCount = 0
    let jsonEnd = -1

    for (let i = 0; i < remaining.length; i++) {
      if (remaining[i] === "{") braceCount++
      else if (remaining[i] === "}") {
        braceCount--
        if (braceCount === 0) {
          jsonEnd = i
          break
        }
      }
    }

    if (jsonEnd === -1) {
      return remaining
    }

    const jsonStr = remaining.substring(0, jsonEnd + 1)
    remaining = remaining.substring(jsonEnd + 1)

    try {
      const parsed = JSON.parse(jsonStr) as unknown
      if (onObject(parsed, jsonStr) === "stop") {
        return remaining
      }
    } catch (error) {
      onParseError?.(jsonStr, error)
    }
  }

  return remaining
}
