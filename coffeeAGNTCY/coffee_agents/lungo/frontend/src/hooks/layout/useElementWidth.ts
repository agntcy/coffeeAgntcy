/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useLayoutEffect, useState, type RefObject } from "react"

/** Tracks `contentRect.width` for a DOM element via `ResizeObserver`. */
export function useElementWidth(
  ref: RefObject<HTMLElement | null>,
): number | undefined {
  const [width, setWidth] = useState<number>()

  useLayoutEffect(() => {
    const element = ref.current
    if (!element) {
      return
    }

    const updateWidth = () => {
      setWidth(element.getBoundingClientRect().width)
    }

    updateWidth()

    const observer = new ResizeObserver(updateWidth)
    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [ref])

  return width
}
