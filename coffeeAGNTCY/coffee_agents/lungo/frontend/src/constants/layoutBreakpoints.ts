/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared layout breakpoint tokens - see docs/open-ui-kit-breakpoints.md.
 */

/** OUK `theme.breakpoints.values.sm` (min-width); compact shell below this width. */
export const LAYOUT_SM_MIN_WIDTH_PX = 600

export function isLayoutWidthBelowSm(widthPx: number): boolean {
  return widthPx < LAYOUT_SM_MIN_WIDTH_PX
}
