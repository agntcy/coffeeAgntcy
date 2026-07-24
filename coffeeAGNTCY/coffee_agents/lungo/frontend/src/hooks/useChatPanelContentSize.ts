/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Sizes the chat panel from the rendered ChatArea content height, then enables
 * fill-height layout so drag-resize can grow the scrollable message region.
 */

import { useLayoutEffect, useState, type RefObject } from "react"
import type { PanelImperativeHandle } from "react-resizable-panels"
import { CHAT_PANEL_AUTO_SIZE_MAX_ATTEMPTS } from "@/components/Chat/chatPanelLayout"

type UseChatPanelContentSizeOptions = {
  enabled: boolean
  chatPanelRef: RefObject<PanelImperativeHandle | null>
  chatContentRef: RefObject<HTMLElement | null>
}

export function useChatPanelContentSize({
  enabled,
  chatPanelRef,
  chatContentRef,
}: UseChatPanelContentSizeOptions) {
  const [contentSized, setContentSized] = useState(false)

  useLayoutEffect(() => {
    if (!enabled) {
      setContentSized(false)
      return
    }

    if (contentSized) {
      return
    }

    let cancelled = false
    let attempts = 0
    let frameId = 0

    const tryResizeToContent = () => {
      if (cancelled) return

      const chatPanel = chatPanelRef.current
      const chatContent = chatContentRef.current
      if (!chatPanel || !chatContent) {
        scheduleRetry()
        return
      }

      const height = Math.ceil(chatContent.getBoundingClientRect().height)
      if (height <= 0) {
        scheduleRetry()
        return
      }

      try {
        chatPanel.resize(`${height}px`)
        if (!cancelled) {
          setContentSized(true)
        }
      } catch {
        scheduleRetry()
      }
    }

    const scheduleRetry = () => {
      if (cancelled || attempts >= CHAT_PANEL_AUTO_SIZE_MAX_ATTEMPTS) {
        return
      }

      attempts += 1
      frameId = window.requestAnimationFrame(tryResizeToContent)
    }

    frameId = window.requestAnimationFrame(tryResizeToContent)

    return () => {
      cancelled = true
      window.cancelAnimationFrame(frameId)
    }
  }, [chatContentRef, chatPanelRef, contentSized, enabled])

  return {
    contentSized,
    fillHeight: enabled && contentSized,
  }
}
