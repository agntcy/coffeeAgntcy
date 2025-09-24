/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, useState, useCallback } from "react"

interface UseChatAreaMeasurementOptions {
  debounceMs?: number
  onHeightChange?: (height: number) => void
}

interface ChatAreaMeasurement {
  height: number
  isExpanded: boolean
  chatRef: React.RefObject<HTMLDivElement | null>
}

export const useChatAreaMeasurement = (
  options: UseChatAreaMeasurementOptions = {},
): ChatAreaMeasurement => {
  const { debounceMs = 150, onHeightChange } = options

  const chatRef = useRef<HTMLDivElement | null>(null)
  const [height, setHeight] = useState(0)
  const [isExpanded, setIsExpanded] = useState(false)
  const debounceTimeoutRef = useRef<number | null>(null)
  const resizeObserverRef = useRef<ResizeObserver | null>(null)

  const debouncedHeightUpdate = useCallback(
    (newHeight: number) => {
      if (debounceTimeoutRef.current) {
        window.clearTimeout(debounceTimeoutRef.current)
      }

      debounceTimeoutRef.current = window.setTimeout(() => {
        const wasExpanded = isExpanded
        const nowExpanded = newHeight > 76

        setHeight(newHeight)
        setIsExpanded(nowExpanded)

        if (
          onHeightChange &&
          (newHeight !== height || wasExpanded !== nowExpanded)
        ) {
          onHeightChange(newHeight)
        }
      }, debounceMs)
    },
    [height, isExpanded, onHeightChange, debounceMs],
  )

  useEffect(() => {
    const chatElement = chatRef.current
    if (!chatElement) return

    resizeObserverRef.current = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { height: newHeight } = entry.contentRect
        debouncedHeightUpdate(newHeight)
      }
    })

    resizeObserverRef.current.observe(chatElement)

    const initialHeight = chatElement.getBoundingClientRect().height
    debouncedHeightUpdate(initialHeight)

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect()
      }
      if (debounceTimeoutRef.current) {
        window.clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [debouncedHeightUpdate])

  return {
    height,
    isExpanded,
    chatRef,
  }
}
