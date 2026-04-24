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
    <div className="w-72 rounded-lg bg-node-background shadow-[var(--shadow-default)_0px_6px_8px] outline outline-1 outline-accent-border">
      <div className="border-accent-border/30 flex items-center justify-between border-b px-4 py-2.5">
        <span className="font-inter text-sm font-medium text-node-text-primary">
          Stories
        </span>
        <button
          onClick={onClose}
          className="text-node-text-secondary opacity-60 transition-opacity hover:opacity-100"
        >
          ✕
        </button>
      </div>

      <div className="max-h-64 overflow-y-auto p-1.5">
        {stories.length === 0 ? (
          <p className="px-2 py-4 text-center font-inter text-sm text-node-text-secondary opacity-60">
            No stories available for this pattern.
          </p>
        ) : (
          stories.map((story) => (
            <button
              key={story.id}
              onClick={() => onSelect(story)}
              className="w-full rounded-md px-3 py-2.5 text-left transition-colors hover:bg-node-background-hover"
            >
              <div className="font-inter text-sm font-normal text-node-text-primary">
                {story.title}
              </div>
              <div className="mt-0.5 font-inter text-xs font-light text-node-text-secondary opacity-70">
                {story.description}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
