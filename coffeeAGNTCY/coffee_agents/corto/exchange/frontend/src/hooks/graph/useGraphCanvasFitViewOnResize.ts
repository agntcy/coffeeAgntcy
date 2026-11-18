/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef } from "react"
import type { ElementSize } from "@/hooks/layout/elementSize"

const DEFAULT_DEBOUNCE_MS = 150

export function useGraphCanvasFitViewOnResize(
  containerSize: ElementSize | undefined,
  fitView: () => void,
  enabled: boolean,
  debounceMs: number = DEFAULT_DEBOUNCE_MS,
): void {
  const fitViewRef = useRef(fitView)
  const debounceTimeoutRef = useRef<number | null>(null)

  useEffect(() => {
    fitViewRef.current = fitView
  }, [fitView])
  const wasEnabledRef = useRef(enabled)

  useEffect(() => {
    const enabledJustTurnedOn = enabled && !wasEnabledRef.current
    wasEnabledRef.current = enabled

    if (!enabled || containerSize === undefined) {
      return
    }

    if (containerSize.width <= 0 || containerSize.height <= 0) {
      return
    }

    if (enabledJustTurnedOn) {
      return
    }

    if (debounceTimeoutRef.current !== null) {
      window.clearTimeout(debounceTimeoutRef.current)
    }

    debounceTimeoutRef.current = window.setTimeout(() => {
      fitViewRef.current()
    }, debounceMs)

    return () => {
      if (debounceTimeoutRef.current !== null) {
        window.clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [
    containerSize?.width,
    containerSize?.height,
    enabled,
    debounceMs,
    containerSize,
  ])
}
