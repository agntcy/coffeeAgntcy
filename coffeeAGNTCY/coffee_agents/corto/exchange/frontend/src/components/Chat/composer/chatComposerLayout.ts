/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { LAYOUT_SM_MIN_WIDTH_PX } from "@/constants/layoutBreakpoints"

export const CHAT_COMPOSER_NARROW_MAX_WIDTH_PX = LAYOUT_SM_MIN_WIDTH_PX - 1
export const CHAT_COMPOSER_STACKED_GAP_PX = 12
export const chatComposerNarrowContainerQuery = `@container chat (max-width: ${CHAT_COMPOSER_NARROW_MAX_WIDTH_PX}px)`
