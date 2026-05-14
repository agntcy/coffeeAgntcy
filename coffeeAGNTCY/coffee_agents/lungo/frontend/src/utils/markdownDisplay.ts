/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Display-only markdown helpers (no extra remark plugins).
 */

/**
 * Turns single newlines in CommonMark prose into hard line breaks (`␠␠\\n`)
 * so `react-markdown` preserves intended line breaks. Fenced ``` blocks are
 * left untouched so code samples are not corrupted.
 */
export function applyHardLineBreaksOutsideFences(markdown: string): string {
  const lines = markdown.split("\n")
  const result: string[] = []
  const proseBuf: string[] = []
  let inFence = false

  const flushProse = () => {
    if (proseBuf.length === 0) {
      return
    }
    const text = proseBuf.join("\n")
    proseBuf.length = 0
    result.push(text.replace(/([^\n])\n(?!\n)/g, "$1  \n"))
  }

  for (const line of lines) {
    if (/^```[\w-]*$/.test(line.trim())) {
      flushProse()
      inFence = !inFence
      result.push(line)
      continue
    }
    if (inFence) {
      result.push(line)
    } else {
      proseBuf.push(line)
    }
  }
  flushProse()
  return result.join("\n")
}
