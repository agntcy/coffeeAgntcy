/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { PatternType } from "@/utils/patternUtils"
import { PATTERNS } from "@/utils/patternUtils"

/**
 * Terminal statuses per pattern. When the auction/streaming status reaches one
 * of these values the runner considers the prompt "done".
 */
const TERMINAL_STATUSES: Partial<Record<PatternType, readonly string[]>> = {
  [PATTERNS.PUBLISH_SUBSCRIBE_STREAMING]: ["completed", "error"],
}

/**
 * Returns `true` when the given status is terminal for the pattern.
 */
export function isTerminalStatus(
  pattern: PatternType,
  status: string,
): boolean {
  const terminals = TERMINAL_STATUSES[pattern]
  return terminals ? terminals.includes(status) : false
}
