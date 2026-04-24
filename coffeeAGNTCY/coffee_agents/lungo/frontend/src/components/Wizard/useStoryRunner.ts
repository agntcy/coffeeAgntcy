/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useEffect, useRef, useState } from "react"
import type { Story, StoryStep } from "@/stories/types"
import { isTerminalStatus } from "@/stories/completion"
import { useStreamingStatus } from "@/stores/auctionStreamingStore"
import { logger } from "@/utils/logger"

export type StoryPhase =
  | "idle"
  | "running"
  | "awaitingCompletion"
  | "dwelling"
  | "narrating"
  | "paused"
  | "done"

export interface StoryRunnerHandles {
  handleDropdownSelect: (query: string) => void
  handleClearConversation: () => void
}

export interface StoryRunnerState {
  phase: StoryPhase
  currentStepIndex: number
  currentNarration: string | null
  isPaused: boolean
  speed: number
  looping: boolean
  totalSteps: number
  play: () => void
  pause: () => void
  next: () => void
  restart: () => void
  exit: () => void
  setLooping: (v: boolean) => void
  setSpeed: (v: number) => void
}

/**
 * Abortable sleep. Resolves `true` on natural completion, `false` if aborted.
 */
function abortableSleep(ms: number, signal: AbortSignal): Promise<boolean> {
  return new Promise((resolve) => {
    if (signal.aborted) {
      resolve(false)
      return
    }
    const id = setTimeout(() => resolve(true), ms)
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(id)
        resolve(false)
      },
      { once: true },
    )
  })
}

export function useStoryRunner(
  story: Story | null,
  handles: StoryRunnerHandles,
): StoryRunnerState {
  const [phase, setPhase] = useState<StoryPhase>("idle")
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [currentNarration, setCurrentNarration] = useState<string | null>(null)
  const [isPaused, setIsPaused] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [looping, setLooping] = useState(false)

  const auctionStatus = useStreamingStatus()

  // Refs for stable access inside the run loop
  const abortRef = useRef<AbortController | null>(null)
  const pauseResolveRef = useRef<(() => void) | null>(null)
  const nextResolveRef = useRef<(() => void) | null>(null)
  const speedRef = useRef(speed)
  const loopingRef = useRef(looping)
  const auctionStatusRef = useRef(auctionStatus)
  const handlesRef = useRef(handles)

  useEffect(() => {
    speedRef.current = speed
  }, [speed])
  useEffect(() => {
    loopingRef.current = looping
  }, [looping])
  useEffect(() => {
    auctionStatusRef.current = auctionStatus
  }, [auctionStatus])
  useEffect(() => {
    handlesRef.current = handles
  }, [handles])

  // Resolve the completion waiter when auction status transitions to terminal
  const completionResolveRef = useRef<(() => void) | null>(null)
  useEffect(() => {
    if (
      story &&
      auctionStatus &&
      isTerminalStatus(story.pattern, auctionStatus) &&
      completionResolveRef.current
    ) {
      completionResolveRef.current()
      completionResolveRef.current = null
    }
  }, [auctionStatus, story])

  /**
   * Wait for the pause gate. If the runner is paused, this promise won't
   * resolve until play() is called.
   */
  const waitForUnpause = useCallback(
    (signal: AbortSignal): Promise<boolean> => {
      return new Promise((resolve) => {
        if (signal.aborted) {
          resolve(false)
          return
        }
        if (!isPausedRef.current) {
          resolve(true)
          return
        }
        pauseResolveRef.current = () => resolve(true)
        signal.addEventListener(
          "abort",
          () => {
            pauseResolveRef.current = null
            resolve(false)
          },
          { once: true },
        )
      })
    },
    [],
  )

  const isPausedRef = useRef(isPaused)
  useEffect(() => {
    isPausedRef.current = isPaused
  }, [isPaused])

  /**
   * Wait for the auction to reach a terminal status, or maxWaitMs.
   */
  const waitForCompletion = useCallback(
    (maxWaitMs: number, signal: AbortSignal): Promise<boolean> => {
      // Already terminal?
      if (story && isTerminalStatus(story.pattern, auctionStatusRef.current)) {
        return Promise.resolve(true)
      }
      return new Promise((resolve) => {
        if (signal.aborted) {
          resolve(false)
          return
        }

        const timeout = setTimeout(() => {
          completionResolveRef.current = null
          logger.warn("[StoryRunner] maxWaitMs elapsed, advancing")
          resolve(true)
        }, maxWaitMs)

        completionResolveRef.current = () => {
          clearTimeout(timeout)
          resolve(true)
        }

        signal.addEventListener(
          "abort",
          () => {
            clearTimeout(timeout)
            completionResolveRef.current = null
            resolve(false)
          },
          { once: true },
        )
      })
    },
    [story],
  )

  /**
   * Wait that can be skipped by pressing Next.
   */
  const skippableWait = useCallback(
    (ms: number, signal: AbortSignal): Promise<boolean> => {
      return new Promise((resolve) => {
        if (signal.aborted) {
          resolve(false)
          return
        }
        const id = setTimeout(() => {
          nextResolveRef.current = null
          resolve(true)
        }, ms)
        nextResolveRef.current = () => {
          clearTimeout(id)
          resolve(true)
        }
        signal.addEventListener(
          "abort",
          () => {
            clearTimeout(id)
            nextResolveRef.current = null
            resolve(false)
          },
          { once: true },
        )
      })
    },
    [],
  )

  /**
   * Process a single step.
   */
  const processStep = useCallback(
    async (step: StoryStep, signal: AbortSignal): Promise<boolean> => {
      const s = speedRef.current
      const defaultPause = story?.defaultPauseAfterMs ?? 2500
      const defaultMaxWait = story?.defaultMaxWaitMs ?? 60_000

      switch (step.kind) {
        case "narration": {
          setPhase("narrating")
          setCurrentNarration(step.text)
          const ok = await skippableWait((step.durationMs ?? 3000) / s, signal)
          setCurrentNarration(null)
          return ok
        }

        case "delay": {
          setPhase("dwelling")
          const ok = await skippableWait(step.ms / s, signal)
          return ok
        }

        case "prompt": {
          if (step.narration) setCurrentNarration(step.narration)
          setPhase("running")

          // Guard: don't dispatch if status is non-idle
          if (
            auctionStatusRef.current !== "idle" &&
            auctionStatusRef.current !== "completed" &&
            auctionStatusRef.current !== "error"
          ) {
            logger.warn(
              "[StoryRunner] Auction not idle, skipping prompt dispatch",
              auctionStatusRef.current,
            )
          }

          handlesRef.current.handleDropdownSelect(step.prompt)

          setPhase("awaitingCompletion")
          const maxWait = step.maxWaitMs ?? defaultMaxWait
          const ok = await waitForCompletion(maxWait, signal)
          if (!ok) return false

          // Dwell after prompt
          setPhase("dwelling")
          setCurrentNarration(null)
          const pauseMs = (step.pauseAfterMs ?? defaultPause) / s
          const dwellOk = await skippableWait(pauseMs, signal)
          return dwellOk
        }

        default:
          return true
      }
    },
    [story, skippableWait, waitForCompletion],
  )

  /**
   * Main run loop. Iterates through all steps, handles looping.
   */
  const runStory = useCallback(
    async (storyToRun: Story) => {
      const ac = new AbortController()
      abortRef.current = ac
      const signal = ac.signal

      setIsPaused(false)
      setCurrentStepIndex(0)
      setCurrentNarration(null)
      setPhase("running")

      let iteration = 0
      do {
        if (iteration > 0) {
          // Loop gap
          setPhase("dwelling")
          setCurrentNarration(null)
          setCurrentStepIndex(0)
          const gapOk = await abortableSleep(8000, signal)
          if (!gapOk) break
          handlesRef.current.handleClearConversation()
        }

        for (let i = 0; i < storyToRun.steps.length; i++) {
          if (signal.aborted) break

          // Pause gate
          const unpauseOk = await waitForUnpause(signal)
          if (!unpauseOk) break

          setCurrentStepIndex(i)
          const ok = await processStep(storyToRun.steps[i], signal)
          if (!ok) break
        }

        if (signal.aborted) break
        iteration++
      } while (loopingRef.current && !signal.aborted)

      if (!signal.aborted) {
        setPhase("done")
      }
    },
    [processStep, waitForUnpause],
  )

  // Auto-start when story is set
  const activeStoryIdRef = useRef<string | null>(null)
  useEffect(() => {
    if (story && story.id !== activeStoryIdRef.current) {
      activeStoryIdRef.current = story.id
      // Abort any existing run
      abortRef.current?.abort()
      runStory(story)
    } else if (!story && activeStoryIdRef.current) {
      activeStoryIdRef.current = null
      abortRef.current?.abort()
      setPhase("idle")
    }
  }, [story, runStory])

  // Controls
  const play = useCallback(() => {
    setIsPaused(false)
    if (pauseResolveRef.current) {
      pauseResolveRef.current()
      pauseResolveRef.current = null
    }
  }, [])

  const pause = useCallback(() => {
    setIsPaused(true)
  }, [])

  const next = useCallback(() => {
    // Only skip narration/delay/dwelling, not awaitingCompletion
    if (nextResolveRef.current) {
      nextResolveRef.current()
      nextResolveRef.current = null
    }
  }, [])

  const restart = useCallback(() => {
    if (!story) return
    abortRef.current?.abort()
    handlesRef.current.handleClearConversation()
    // Small delay to let cleanup propagate
    setTimeout(() => runStory(story), 50)
  }, [story, runStory])

  const exit = useCallback(() => {
    abortRef.current?.abort()
    activeStoryIdRef.current = null
    setPhase("idle")
    setCurrentStepIndex(0)
    setCurrentNarration(null)
    setIsPaused(false)
    handlesRef.current.handleClearConversation()
  }, [])

  return {
    phase,
    currentStepIndex,
    currentNarration,
    isPaused,
    speed,
    looping,
    totalSteps: story?.steps.length ?? 0,
    play,
    pause,
    next,
    restart,
    exit,
    setLooping,
    setSpeed,
  }
}
