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
      pauseAfterMs?: number
      maxWaitMs?: number
    }
  | { kind: "narration"; text: string; durationMs?: number }
  | { kind: "delay"; ms: number }

export interface Story {
  id: string
  title: string
  description: string
  pattern: PatternType
  defaultPauseAfterMs?: number
  defaultMaxWaitMs?: number
  steps: StoryStep[]
}
