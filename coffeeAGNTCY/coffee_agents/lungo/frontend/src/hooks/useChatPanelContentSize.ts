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

const COMPOSER_RESIZE_DEBOUNCE_MS = 150

type UseChatPanelContentSizeOptions = {
  enabled: boolean
  /** When this value changes, panel height is re-measured from chat content. */
  remeasureKey?: unknown
  /**
   * When false (composer-only), measure intrinsic scroll height and do not
   * stretch the chat shell to the panel (avoids feedback with persisted flex).
   */
  fillPanelHeight?: boolean
  chatPanelRef: RefObject<PanelImperativeHandle | null>
  chatContentRef: RefObject<HTMLElement | null>
}

export function useChatPanelContentSize({
  enabled,
  remeasureKey,
  fillPanelHeight = true,
  chatPanelRef,
  chatContentRef,
}: UseChatPanelContentSizeOptions) {
  const [contentSized, setContentSized] = useState(false)

  useLayoutEffect(() => {
    if (!enabled) {
      setContentSized(false)
      return
    }

    setContentSized(false)

    let cancelled = false
    let attempts = 0
    let frameId = 0
    let contentResizeObserver: ResizeObserver | null = null
    let composerResizeDebounceId: number | null = null
    let lastAppliedHeight = -1

    const measureContentHeight = (chatContent: HTMLElement) => {
      if (fillPanelHeight) {
        return Math.ceil(chatContent.getBoundingClientRect().height)
      }

      const composerRegion = chatContent.querySelector(
        "[data-chat-composer-region]",
      )
      if (composerRegion instanceof HTMLElement) {
        const chatStyles = getComputedStyle(chatContent)
        const borderTop = parseFloat(chatStyles.borderTopWidth) || 0
        const borderBottom = parseFloat(chatStyles.borderBottomWidth) || 0
        return Math.ceil(
          borderTop +
            composerRegion.offsetTop +
            composerRegion.offsetHeight +
            borderBottom,
        )
      }

      return Math.ceil(
        Math.max(
          chatContent.scrollHeight,
          chatContent.offsetHeight,
          chatContent.getBoundingClientRect().height,
        ),
      )
    }

    const resizePanelToContent = (): boolean => {
      if (cancelled) return false

      const chatPanel = chatPanelRef.current
      const chatContent = chatContentRef.current
      if (!chatPanel || !chatContent) {
        return false
      }

      const height = measureContentHeight(chatContent)
      if (height <= 0) {
        return false
      }

      if (height === lastAppliedHeight) {
        if (!cancelled) {
          setContentSized(true)
        }
        return true
      }

      try {
        chatPanel.resize(`${height}px`)
        lastAppliedHeight = height
        if (!cancelled) {
          setContentSized(true)
        }
        return true
      } catch {
        return false
      }
    }

    const observeContentHeight = (chatContent: HTMLElement) => {
      if (fillPanelHeight || contentResizeObserver) {
        return
      }

      const composerRegion = chatContent.querySelector(
        "[data-chat-composer-region]",
      )
      if (!(composerRegion instanceof HTMLElement)) {
        return
      }

      contentResizeObserver = new ResizeObserver(() => {
        if (cancelled) return
        if (composerResizeDebounceId !== null) {
          window.clearTimeout(composerResizeDebounceId)
        }
        composerResizeDebounceId = window.setTimeout(() => {
          composerResizeDebounceId = null
          if (cancelled) return
          frameId = window.requestAnimationFrame(() => {
            resizePanelToContent()
          })
        }, COMPOSER_RESIZE_DEBOUNCE_MS)
      })
      contentResizeObserver.observe(composerRegion)
    }

    const tryResizeToContent = () => {
      if (cancelled) return

      const chatContent = chatContentRef.current
      if (!resizePanelToContent()) {
        scheduleRetry()
        return
      }

      if (chatContent) {
        observeContentHeight(chatContent)
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
      if (composerResizeDebounceId !== null) {
        window.clearTimeout(composerResizeDebounceId)
      }
      contentResizeObserver?.disconnect()
    }
  }, [chatContentRef, chatPanelRef, enabled, fillPanelHeight, remeasureKey])

  return {
    contentSized,
    fillHeight: enabled && contentSized && fillPanelHeight,
  }
}
