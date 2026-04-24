/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { createContext, useContext } from "react"
import type { Story } from "@/stories/types"
import type { PatternType } from "@/utils/patternUtils"

export interface StoryContextValue {
  activeStory: Story | null
  setActiveStory: (story: Story | null) => void
  selectedPattern: PatternType
  handleDropdownSelect: (query: string) => void
  handleClearConversation: () => void
}

export const StoryContext = createContext<StoryContextValue | null>(null)

export function useStoryContext(): StoryContextValue {
  const ctx = useContext(StoryContext)
  if (!ctx) {
    throw new Error(
      "useStoryContext must be used within a StoryContext.Provider",
    )
  }
  return ctx
}
