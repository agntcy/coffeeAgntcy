/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { fetchJson, isHttpError } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import type { HttpRequestTarget } from "@/urls"
import type { PromptCategory, SuggestedPromptsResponse } from "./PromptTypes"
import {
  getRetryDelayMs,
  MAX_SUGGESTED_PROMPTS_RETRIES,
  parsePromptCategories,
} from "./suggestedPromptsUtils"

interface UseSuggestedPromptsResult {
  categories: PromptCategory[]
  isLoading: boolean
  isUnavailable: boolean
}

function hasPrompts(categories: PromptCategory[]): boolean {
  return categories.some((category) => category.prompts.length > 0)
}

export function useSuggestedPrompts(
  request: HttpRequestTarget | null | undefined,
): UseSuggestedPromptsResult {
  const [categories, setCategories] = useState<PromptCategory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUnavailable, setIsUnavailable] = useState(false)
  const url = request?.url ?? null
  const endpointLabel = request?.endpointLabel ?? null

  useEffect(() => {
    if (!url || !endpointLabel) {
      setCategories([])
      setIsLoading(false)
      setIsUnavailable(false)
      return
    }

    const controller = new AbortController()
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null
    let cancelled = false

    const markUnavailable = (error: unknown) => {
      if (cancelled) return
      reportRequestError(endpointLabel, error)
      setCategories([])
      setIsUnavailable(true)
      setIsLoading(false)
    }

    const scheduleRetry = (retryCount: number, run: () => void) => {
      retryTimeoutId = setTimeout(run, getRetryDelayMs(retryCount))
    }

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        setIsUnavailable(false)

        const data = await fetchJson<SuggestedPromptsResponse>(url, {
          endpointLabel,
          cache: "no-cache",
          signal: controller.signal,
        })

        const nextCategories = parsePromptCategories(data)

        if (!hasPrompts(nextCategories)) {
          if (retryCount >= MAX_SUGGESTED_PROMPTS_RETRIES) {
            markUnavailable(
              new Error("Suggested prompts response contained no prompts"),
            )
            return
          }
          scheduleRetry(retryCount, () => {
            void fetchPrompts(retryCount + 1)
          })
          return
        }

        setCategories(nextCategories)
        setIsLoading(false)
      } catch (err: unknown) {
        if (cancelled) return
        if (isHttpError(err) && err.message === "Request was cancelled.") {
          return
        }
        if (err instanceof DOMException && err.name === "AbortError") {
          return
        }

        if (retryCount >= MAX_SUGGESTED_PROMPTS_RETRIES) {
          markUnavailable(err)
          return
        }

        scheduleRetry(retryCount, () => {
          void fetchPrompts(retryCount + 1)
        })
      }
    }

    void fetchPrompts()

    return () => {
      cancelled = true
      controller.abort()
      if (retryTimeoutId) {
        clearTimeout(retryTimeoutId)
      }
    }
  }, [url, endpointLabel])

  return { categories, isLoading, isUnavailable }
}
