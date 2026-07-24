/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { logger } from "@/utils/logger"
import type { PromptCategory } from "./PromptTypes"
import { getRetryDelayMs, parsePromptCategories } from "./suggestedPromptsUtils"

interface UseSuggestedPromptsResult {
  categories: PromptCategory[]
  isLoading: boolean
}

export function useSuggestedPrompts(
  promptsUrl: string | null | undefined,
): UseSuggestedPromptsResult {
  const [categories, setCategories] = useState<PromptCategory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const url = promptsUrl ?? null

  useEffect(() => {
    if (!url) {
      setCategories([])
      setIsLoading(false)
      return
    }

    const controller = new AbortController()
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        const res = await fetch(url, {
          cache: "no-cache",
          signal: controller.signal,
        })

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }

        const data: unknown = await res.json()
        const nextCategories = parsePromptCategories(data)
        setCategories(nextCategories)

        if (nextCategories.every((category) => category.prompts.length === 0)) {
          retryTimeoutId = setTimeout(
            () => fetchPrompts(retryCount + 1),
            getRetryDelayMs(retryCount),
          )
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          logger.warn("Failed to load suggested prompts.", err)
          retryTimeoutId = setTimeout(
            () => fetchPrompts(retryCount + 1),
            getRetryDelayMs(retryCount),
          )
        }
      } finally {
        setIsLoading(false)
      }
    }

    fetchPrompts()

    return () => {
      controller.abort()
      if (retryTimeoutId) {
        clearTimeout(retryTimeoutId)
      }
    }
  }, [url])

  return { categories, isLoading }
}
