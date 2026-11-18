/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export const LAYOUT_SM_MIN_WIDTH_PX = 600

export function isLayoutWidthBelowSm(widthPx: number): boolean {
  return widthPx < LAYOUT_SM_MIN_WIDTH_PX
}
