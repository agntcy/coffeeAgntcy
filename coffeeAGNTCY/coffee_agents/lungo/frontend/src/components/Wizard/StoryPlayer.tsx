/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Story } from "@/stories/types"
import { useStoryRunner, type StoryRunnerHandles } from "./useStoryRunner"

interface StoryPlayerProps {
  story: Story
  handles: StoryRunnerHandles
  onExit: () => void
}

const SPEED_OPTIONS = [0.5, 1, 2] as const

export default function StoryPlayer({
  story,
  handles,
  onExit,
}: StoryPlayerProps) {
  const runner = useStoryRunner(story, handles)

  const handleExit = () => {
    runner.exit()
    onExit()
  }

  return (
    <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Phase indicator */}
          <span className="text-lg">
            {runner.phase === "done" ? "✓" : runner.isPaused ? "⏸" : "▶"}
          </span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {story.title}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Step {runner.currentStepIndex + 1}/{runner.totalSteps}
          </span>
          <button
            onClick={handleExit}
            className="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
          >
            ✕ Exit
          </button>
        </div>
      </div>

      {/* Narration */}
      {runner.currentNarration && (
        <p className="mt-1 text-sm italic text-gray-600 dark:text-gray-300">
          &ldquo;{runner.currentNarration}&rdquo;
        </p>
      )}

      {/* Controls row */}
      <div className="mt-2 flex items-center gap-2">
        {/* Play / Pause */}
        <button
          onClick={runner.isPaused ? runner.play : runner.pause}
          disabled={runner.phase === "done"}
          className="rounded bg-gray-200 px-3 py-1 text-sm font-medium hover:bg-gray-300 disabled:opacity-40 dark:bg-gray-700 dark:hover:bg-gray-600"
        >
          {runner.isPaused ? "▶ Resume" : "⏸ Pause"}
        </button>

        {/* Next */}
        <button
          onClick={runner.next}
          disabled={
            runner.phase === "done" || runner.phase === "awaitingCompletion"
          }
          title={
            runner.phase === "awaitingCompletion"
              ? "Waiting for stream to complete"
              : undefined
          }
          className="rounded bg-gray-200 px-3 py-1 text-sm font-medium hover:bg-gray-300 disabled:opacity-40 dark:bg-gray-700 dark:hover:bg-gray-600"
        >
          ⏭ Next
        </button>

        {/* Restart */}
        <button
          onClick={runner.restart}
          className="rounded bg-gray-200 px-3 py-1 text-sm font-medium hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600"
        >
          ↺ Restart
        </button>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Loop toggle */}
        <label className="flex cursor-pointer items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
          Loop
          <input
            type="checkbox"
            checked={runner.looping}
            onChange={(e) => runner.setLooping(e.target.checked)}
            className="ml-1"
          />
        </label>

        {/* Speed select */}
        <label className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
          Speed
          <select
            value={runner.speed}
            onChange={(e) => runner.setSpeed(Number(e.target.value))}
            className="rounded border border-gray-300 bg-white px-1 py-0.5 text-sm dark:border-gray-600 dark:bg-gray-700"
          >
            {SPEED_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}x
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}
