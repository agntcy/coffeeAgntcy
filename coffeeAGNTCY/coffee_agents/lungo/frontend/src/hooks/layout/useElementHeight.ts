/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useLayoutEffect, useState, type RefObject } from "react"

/** Tracks `contentRect.height` for a DOM element via `ResizeObserver`. */
export function useElementHeight(
  ref: RefObject<HTMLElement | null>,
): number | undefined {
  const [height, setHeight] = useState<number>()

  useLayoutEffect(() => {
    const element = ref.current
    if (!element) {
      return
    }

    const updateHeight = () => {
      setHeight(element.getBoundingClientRect().height)
    }

    updateHeight()

    const observer = new ResizeObserver(updateHeight)
    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [ref])

  return height
}
