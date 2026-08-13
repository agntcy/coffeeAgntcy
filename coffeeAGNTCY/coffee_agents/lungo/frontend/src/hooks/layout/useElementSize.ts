/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useLayoutEffect, useState, type RefObject } from "react"

export interface ElementSize {
  width: number
  height: number
}

/** Tracks `contentRect` width and height for a DOM element via `ResizeObserver`. */
export function useElementSize(
  ref: RefObject<HTMLElement | null>,
): ElementSize | undefined {
  const [size, setSize] = useState<ElementSize>()

  useLayoutEffect(() => {
    const element = ref.current
    if (!element) {
      return
    }

    const updateSize = () => {
      const { width, height } = element.getBoundingClientRect()
      setSize((prev) =>
        prev?.width === width && prev?.height === height
          ? prev
          : { width, height },
      )
    }

    updateSize()

    const observer = new ResizeObserver(updateSize)
    observer.observe(element)
    window.addEventListener("resize", updateSize)

    return () => {
      observer.disconnect()
      window.removeEventListener("resize", updateSize)
    }
  }, [ref])

  return size
}
