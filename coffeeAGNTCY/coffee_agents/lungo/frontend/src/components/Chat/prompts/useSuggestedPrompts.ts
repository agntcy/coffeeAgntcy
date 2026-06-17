/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { logger } from "@/utils/logger"
import type { PromptCategory } from "./PromptTypes"
import {
  getRetryDelayMs,
  getSuggestedPromptsUrl,
  parsePromptCategories,
  type SuggestedPromptsSource,
} from "./suggestedPromptsUtils"

interface UseSuggestedPromptsResult {
  categories: PromptCategory[]
  isLoading: boolean
}

export function useSuggestedPrompts(
  source: SuggestedPromptsSource,
  pattern?: string,
): UseSuggestedPromptsResult {
  const [categories, setCategories] = useState<PromptCategory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const url = getSuggestedPromptsUrl(source, pattern)

  useEffect(() => {
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
          logger.warn(`Failed to load ${source} suggested prompts.`, err)
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
  }, [source, url])

  return { categories, isLoading }
}
