/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Re-fit the workflow graph when the canvas container changes size (sidebar drag,
 * window resize, chat panel drag, compact controls bar, etc.).
 */

import { useEffect, useRef } from "react"
import type { ElementSize } from "@/hooks/layout/useElementSize"

const DEFAULT_DEBOUNCE_MS = 150

export function useGraphCanvasFitViewOnResize(
  containerSize: ElementSize | undefined,
  fitView: () => void,
  enabled: boolean,
  debounceMs: number = DEFAULT_DEBOUNCE_MS,
): void {
  const fitViewRef = useRef(fitView)
  fitViewRef.current = fitView
  const debounceTimeoutRef = useRef<number | null>(null)

  useEffect(() => {
    if (!enabled || containerSize === undefined) {
      return
    }

    if (containerSize.width <= 0 || containerSize.height <= 0) {
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
