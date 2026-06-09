/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Scroll helpers for the chat message panel.
 */

import { useEffect, type RefObject } from "react"

export function scrollElementToBottom(
  element: HTMLElement | null | undefined,
  behavior: "auto" | "instant" | "smooth" = "smooth",
): void {
  if (!element) return
  element.scrollTo({ top: element.scrollHeight, behavior })
}

/** Run scroll after layout so newly rendered message content is measured. */
export function scheduleScrollElementToBottom(
  element: HTMLElement | null | undefined,
  behavior: "auto" | "instant" | "smooth" = "smooth",
): void {
  if (!element) return
  requestAnimationFrame(() => {
    scrollElementToBottom(element, behavior)
  })
}

/**
 * Scroll the message panel when thread content grows (streaming, new messages, etc.).
 */
export function useScrollPanelOnContentResize(
  scrollPanelRef: RefObject<HTMLElement | null>,
  contentRef: RefObject<HTMLElement | null>,
  enabled: boolean,
): void {
  useEffect(() => {
    if (!enabled) return

    const panel = scrollPanelRef.current
    const content = contentRef.current
    if (!panel || !content) return

    scheduleScrollElementToBottom(panel)

    let lastHeight = content.getBoundingClientRect().height

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const newHeight = entry.contentRect.height
        if (newHeight > lastHeight) {
          scheduleScrollElementToBottom(panel)
        }
        lastHeight = newHeight
      }
    })

    observer.observe(content)
    return () => observer.disconnect()
  }, [scrollPanelRef, contentRef, enabled])
}
