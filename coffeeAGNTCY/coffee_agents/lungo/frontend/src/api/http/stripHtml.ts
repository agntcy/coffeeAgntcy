/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import DOMPurify from "dompurify"

/**
 * Strip HTML tags so the result is safe to render as text.
 * Used for API/backend error strings before display to prevent XSS if backend sends HTML.
 * Uses DOMPurify when DOM is available (accurate parsing); falls back to regex in Node (e.g. tests).
 */
export function stripHtml(html: string): string {
  if (typeof html !== "string" || html.length === 0) return html
  if (typeof window !== "undefined") {
    try {
      const out = DOMPurify.sanitize(html, { ALLOWED_TAGS: [] })
      return out.replace(/\s+/g, " ").trim()
    } catch {
      // fallback if DOMPurify fails (e.g. no DOM in tests)
    }
  }
  let out = html.replace(/<[^>]*>/g, " ")
  out = out.replace(/\s+/g, " ").trim()
  const entities: Record<string, string> = {
    "&lt;": "<",
    "&gt;": ">",
    "&amp;": "&",
    "&quot;": '"',
    "&#39;": "'",
    "&apos;": "'",
  }
  for (const [ent, char] of Object.entries(entities)) {
    out = out.split(ent).join(char)
  }
  out = out.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
  out = out.replace(/&#x([0-9a-fA-F]+);/g, (_, n) =>
    String.fromCharCode(parseInt(n, 16)),
  )
  return out
}
