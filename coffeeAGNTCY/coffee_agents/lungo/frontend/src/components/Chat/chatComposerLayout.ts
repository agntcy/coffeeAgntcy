/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * `@container chat` inline-size query - matches layout `sm` (600px min-width).
 */

import { LAYOUT_SM_MIN_WIDTH_PX } from "@/constants/layoutBreakpoints"

/** Max width for stacked composer layout inside the `chat` container (width strictly below `sm`). */
export const CHAT_COMPOSER_NARROW_MAX_WIDTH_PX = LAYOUT_SM_MIN_WIDTH_PX - 1

/** Vertical gap between stacked composer controls (prompts, input, send). */
export const CHAT_COMPOSER_STACKED_GAP_PX = 12

export const chatComposerNarrowContainerQuery = `@container chat (max-width: ${CHAT_COMPOSER_NARROW_MAX_WIDTH_PX}px)`
