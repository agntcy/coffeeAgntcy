/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState } from "react"
import { ChevronDown, ChevronUp, LoaderCircle } from "lucide-react"
import type { Story, StoryStep } from "@/stories/types"
import { useStoryRunner, type StoryRunnerHandles } from "./useStoryRunner"

interface StoryPlayerProps {
  story: Story
  handles: StoryRunnerHandles
  onExit: () => void
}

const SPEED_OPTIONS = [0.5, 1, 2] as const

function stepLabel(step: StoryStep, index: number): string {
  switch (step.kind) {
    case "prompt":
      return `${index + 1}. Prompt: ${step.prompt}`
    case "narration":
      return `${index + 1}. Narration`
    case "delay":
      return `${index + 1}. Delay (${step.ms}ms)`
  }
}

export default function StoryPlayer({
  story,
  handles,
  onExit,
}: StoryPlayerProps) {
  const runner = useStoryRunner(story, handles)
  const [sequenceOpen, setSequenceOpen] = useState(false)

  const handleExit = () => {
    runner.exit()
    onExit()
  }

  const isActive =
    runner.phase !== "idle" && runner.phase !== "done" && !runner.isPaused

  const currentStep = story.steps[runner.currentStepIndex]

  return (
    <div className="px-4 py-3">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-node-icon-background">
            {isActive ? (
              <LoaderCircle className="h-3.5 w-3.5 animate-spin text-accent-primary" />
            ) : (
              <span className="text-xs text-accent-primary">
                {runner.phase === "done" ? "✓" : "⏸"}
              </span>
            )}
          </div>
          <span className="font-inter text-sm font-normal leading-5 text-node-text-primary">
            {story.title}
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          {isActive && (
            <LoaderCircle className="h-3 w-3 animate-spin text-accent-primary" />
          )}
          <button
            onClick={() => setSequenceOpen((v) => !v)}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 font-inter text-xs text-node-text-secondary transition-colors hover:bg-node-background-hover"
          >
            Step {runner.currentStepIndex + 1}/{runner.totalSteps}
            {sequenceOpen ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </button>
          <button
            onClick={handleExit}
            className="rounded px-1.5 py-0.5 font-inter text-xs text-node-text-secondary opacity-60 transition-opacity hover:opacity-100"
          >
            ✕ Exit
          </button>
        </div>
      </div>

      {/* Narration */}
      {runner.currentNarration && (
        <p className="mt-1.5 font-inter text-xs font-light italic text-node-text-secondary opacity-80">
          &ldquo;{runner.currentNarration}&rdquo;
        </p>
      )}

      {/* Current step dialogue */}
      {currentStep?.dialogue && !sequenceOpen && (
        <p className="mt-1.5 font-inter text-xs font-light leading-4 text-node-text-secondary opacity-70">
          {currentStep.dialogue}
        </p>
      )}

      {/* Step sequence dropdown */}
      {sequenceOpen && (
        <div className="bg-node-icon-background/50 mt-2 max-h-48 overflow-y-auto rounded-md p-1.5">
          {story.steps.map((step, i) => {
            const isCurrent = i === runner.currentStepIndex
            const isPast = i < runner.currentStepIndex
            return (
              <div
                key={i}
                className={`rounded-md px-2.5 py-1.5 ${isCurrent ? "outline-accent-border/40 bg-node-background-hover outline outline-1" : ""}`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`font-inter text-xs ${
                      isCurrent
                        ? "font-medium text-accent-primary"
                        : isPast
                          ? "text-node-text-secondary opacity-50"
                          : "text-node-text-secondary"
                    }`}
                  >
                    {isPast ? "✓" : isCurrent ? "›" : "○"}
                  </span>
                  <span
                    className={`font-inter text-xs ${
                      isCurrent
                        ? "font-medium text-node-text-primary"
                        : isPast
                          ? "text-node-text-secondary line-through opacity-50"
                          : "text-node-text-secondary"
                    }`}
                  >
                    {stepLabel(step, i)}
                  </span>
                </div>
                {step.dialogue && isCurrent && (
                  <p className="mt-1 pl-5 font-inter text-xs font-light leading-4 text-node-text-secondary opacity-70">
                    {step.dialogue}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Controls row */}
      <div className="mt-2.5 flex items-center gap-1.5">
        <button
          onClick={runner.isPaused ? runner.play : runner.pause}
          disabled={runner.phase === "done"}
          className="rounded-md bg-node-icon-background px-2.5 py-1 font-inter text-xs font-normal text-node-text-primary transition-colors hover:bg-node-background-hover disabled:opacity-30"
        >
          {runner.isPaused ? "▶ Resume" : "⏸ Pause"}
        </button>

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
          className="rounded-md bg-node-icon-background px-2.5 py-1 font-inter text-xs font-normal text-node-text-primary transition-colors hover:bg-node-background-hover disabled:opacity-30"
        >
          ⏭ Next
        </button>

        <button
          onClick={runner.restart}
          className="rounded-md bg-node-icon-background px-2.5 py-1 font-inter text-xs font-normal text-node-text-primary transition-colors hover:bg-node-background-hover"
        >
          ↺ Restart
        </button>

        <div className="flex-1" />

        <label className="flex cursor-pointer items-center gap-1 font-inter text-xs text-node-text-secondary">
          Loop
          <input
            type="checkbox"
            checked={runner.looping}
            onChange={(e) => runner.setLooping(e.target.checked)}
            className="accent-accent-primary"
          />
        </label>

        <label className="flex items-center gap-1 font-inter text-xs text-node-text-secondary">
          Speed
          <select
            value={runner.speed}
            onChange={(e) => runner.setSpeed(Number(e.target.value))}
            className="rounded-md border-0 bg-node-icon-background px-1 py-0.5 font-inter text-xs text-node-text-primary outline-none"
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
