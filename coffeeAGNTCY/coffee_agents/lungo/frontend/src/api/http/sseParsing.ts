/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export function parseSseDataLine<T>(line: string): T | null {
  const trimmed = line.trim()
  if (!trimmed.startsWith("data:")) return null
  const jsonPart = trimmed.slice(5).trim()
  if (!jsonPart) return null
  try {
    return JSON.parse(jsonPart) as T
  } catch {
    return null
  }
}

export function splitSseFrames(buffer: string): {
  frames: string[]
  remainder: string
} {
  const frames: string[] = []
  let rest = buffer
  let idx: number
  while ((idx = rest.indexOf("\n\n")) !== -1) {
    frames.push(rest.slice(0, idx))
    rest = rest.slice(idx + 2)
  }
  return { frames, remainder: rest }
}

export function parseSseFrameLines<T>(frame: string): T[] {
  const events: T[] = []
  const lines = frame.split("\n")
  for (const line of lines) {
    if (!line.length || line.startsWith(":")) continue
    const ev = parseSseDataLine<T>(line)
    if (ev) events.push(ev)
  }
  return events
}
