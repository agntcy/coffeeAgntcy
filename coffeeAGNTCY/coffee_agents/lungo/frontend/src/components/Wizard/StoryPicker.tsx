/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Story } from "@/stories/types"
import type { PatternType } from "@/utils/patternUtils"
import { storyRegistry } from "@/stories"

interface StoryPickerProps {
  pattern: PatternType
  onSelect: (story: Story) => void
  onClose: () => void
}

export default function StoryPicker({
  pattern,
  onSelect,
  onClose,
}: StoryPickerProps) {
  const stories = storyRegistry[pattern] ?? []

  return (
    <div className="absolute right-4 top-14 z-30 w-72 rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2 dark:border-gray-700">
        <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
          Stories
        </span>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          ✕
        </button>
      </div>

      <div className="max-h-64 overflow-y-auto p-2">
        {stories.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-gray-400">
            No stories available for this pattern.
          </p>
        ) : (
          stories.map((story) => (
            <button
              key={story.id}
              onClick={() => onSelect(story)}
              className="w-full rounded-md px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <div className="text-sm font-medium text-gray-800 dark:text-gray-200">
                {story.title}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {story.description}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
