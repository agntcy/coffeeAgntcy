/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { PatternType } from "@/utils/patternUtils"

export type StoryStep =
  | {
      kind: "prompt"
      prompt: string
      narration?: string
      dialogue?: string
      pauseAfterMs?: number
      maxWaitMs?: number
    }
  | { kind: "narration"; text: string; dialogue?: string; durationMs?: number }
  | { kind: "delay"; ms: number; dialogue?: string }

export interface Story {
  id: string
  title: string
  description: string
  pattern: PatternType
  defaultPauseAfterMs?: number
  defaultMaxWaitMs?: number
  steps: StoryStep[]
}
