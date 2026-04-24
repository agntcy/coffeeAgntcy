/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState } from "react"
import type { Story } from "@/stories/types"
import type { PatternType } from "@/utils/patternUtils"
import StoryPicker from "./StoryPicker"

interface WizardFabProps {
  selectedPattern: PatternType
  onSelectStory: (story: Story) => void
}

export default function WizardFab({
  selectedPattern,
  onSelectStory,
}: WizardFabProps) {
  const [pickerOpen, setPickerOpen] = useState(false)

  const handleSelect = (story: Story) => {
    setPickerOpen(false)
    onSelectStory(story)
  }

  return (
    <div className="absolute right-4 top-4 z-20">
      <button
        onClick={() => setPickerOpen((v) => !v)}
        className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        title="Workflow Wizard"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {pickerOpen && (
        <StoryPicker
          pattern={selectedPattern}
          onSelect={handleSelect}
          onClose={() => setPickerOpen(false)}
        />
      )}
    </div>
  )
}
