/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared inset tokens for main-area presentations (graph control bar, pattern
 * doc canvas, chat). Keeps horizontal rhythm aligned across panes.
 */

/** Horizontal padding shared by graph control bar, pattern doc canvas, and chat. */
export const mainAreaContentHorizontalPadding = {
  xs: 2,
  sm: 4,
  md: 8,
  lg: 15,
} as const

export type MainAreaContentHorizontalPadding =
  typeof mainAreaContentHorizontalPadding

/** Vertical padding for pattern doc header/body sections. */
export const mainAreaContentVerticalPadding = {
  xs: 1.5,
  sm: 2,
} as const

/** Vertical padding for pattern doc outer frame (above/below the card). */
export const mainAreaContentOuterVerticalPadding = {
  xs: 1,
  sm: 1.5,
} as const
