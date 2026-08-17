/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * `@container chat` inline-size query — matches layout `sm` (600px min-width).
 */

/** Max width for stacked composer layout inside the `chat` container (width strictly below 600px). */
export const CHAT_COMPOSER_NARROW_MAX_WIDTH_PX = 599

/** Vertical gap between stacked composer controls (prompts, input, send). */
export const CHAT_COMPOSER_STACKED_GAP_PX = 12

export const chatComposerNarrowContainerQuery = `@container chat (max-width: ${CHAT_COMPOSER_NARROW_MAX_WIDTH_PX}px)`
