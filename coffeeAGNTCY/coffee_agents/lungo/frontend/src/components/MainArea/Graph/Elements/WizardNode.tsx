/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState } from "react"
import { useStoryContext } from "@/contexts/StoryContext"
import { getPatternDisplayName } from "@/utils/patternUtils"
import StoryPicker from "@/components/Wizard/StoryPicker"
import StoryPlayer from "@/components/Wizard/StoryPlayer"

export default function WizardNode() {
  const {
    activeStory,
    setActiveStory,
    selectedPattern,
    handleDropdownSelect,
    handleClearConversation,
  } = useStoryContext()

  const [pickerOpen, setPickerOpen] = useState(false)
  const wizardTitle = `${getPatternDisplayName(selectedPattern)} Workflow Wizard`

  if (activeStory) {
    return (
      <div className="w-[420px] rounded-lg bg-node-background shadow-[var(--shadow-default)_0px_6px_8px] outline outline-2 outline-accent-border">
        <StoryPlayer
          story={activeStory}
          handles={{ handleDropdownSelect, handleClearConversation }}
          onExit={() => setActiveStory(null)}
        />
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setPickerOpen((v) => !v)}
        className="flex items-center gap-2.5 rounded-lg bg-node-background px-4 py-3 shadow-[var(--shadow-default)_0px_4px_6px] outline outline-1 outline-accent-border transition-all hover:bg-node-background-hover hover:shadow-[var(--shadow-default)_0px_6px_8px] hover:outline-2"
      >
        <div className="flex h-5 w-5 items-center justify-center rounded bg-node-icon-background">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-3.5 w-3.5 text-accent-primary"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <span className="font-inter text-sm font-normal leading-5 text-node-text-primary">
          {wizardTitle}
        </span>
      </button>

      {pickerOpen && (
        <div className="absolute left-0 top-full z-50 mt-2">
          <StoryPicker
            pattern={selectedPattern}
            onSelect={(story) => {
              setPickerOpen(false)
              setActiveStory(story)
            }}
            onClose={() => setPickerOpen(false)}
          />
        </div>
      )}
    </div>
  )
}
