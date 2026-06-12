/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useLayoutEffect, useState, type RefObject } from "react"

export interface ElementRectSnapshot {
  left: number
  width: number
}

/** Tracks layout box (`left`, `width`) for a DOM element. */
export function useElementRect(
  ref: RefObject<HTMLElement | null>,
): ElementRectSnapshot | undefined {
  const [rect, setRect] = useState<ElementRectSnapshot>()

  useLayoutEffect(() => {
    const element = ref.current
    if (!element) {
      return
    }

    const updateRect = () => {
      const next = element.getBoundingClientRect()
      setRect({ left: next.left, width: next.width })
    }

    updateRect()

    const observer = new ResizeObserver(updateRect)
    observer.observe(element)
    window.addEventListener("resize", updateRect)

    return () => {
      observer.disconnect()
      window.removeEventListener("resize", updateRect)
    }
  }, [ref])

  return rect
}
