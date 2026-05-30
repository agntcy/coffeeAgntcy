/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useMemo, useState } from "react"
import { Dropdown } from "@open-ui-kit/core"
import { env } from "@/utils/env"
import { logger } from "@/utils/logger"
import { CustomDropdownListItemContent } from "./CustomDropdownListItemContent"
import { PromptCategory } from "./PromptTypes"

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  env.get("VITE_EXCHANGE_APP_API_URL") || DEFAULT_EXCHANGE_APP_API_URL

interface CoffeePromptsDropdownProps {
  onSelect: (query: string) => void
  pattern?: string
}

const CoffeePromptsDropdown: React.FC<CoffeePromptsDropdownProps> = ({
  onSelect,
  pattern,
}) => {
  const [categories, setCategories] = useState<PromptCategory[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Fetch prompts on mount or pattern change
  useEffect(() => {
    const controller = new AbortController()
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null
    const MAX_RETRY_DELAY = 5000 // 5 seconds max

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        const isStreamingPattern = pattern === "publish_subscribe_streaming"
        const url = isStreamingPattern
          ? `${EXCHANGE_APP_API_URL}/suggested-prompts?pattern=streaming`
          : `${EXCHANGE_APP_API_URL}/suggested-prompts`

        const res = await fetch(url, {
          cache: "no-cache",
          signal: controller.signal,
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data: unknown = await res.json()

        logger.debug("Fetched prompts data:", data)

        const categories =
          data !== null && typeof data === "object" && !Array.isArray(data)
            ? Object.entries(data as Record<string, unknown>).map(
                ([key, value]) => ({
                  name: key,
                  prompts: Array.isArray(value) ? value : [],
                }),
              )
            : []
        setCategories(categories)

        // Retry if all categories are empty
        if (categories.every((category) => category.prompts.length === 0)) {
          const delay = Math.min(
            5000 * Math.pow(2, retryCount),
            MAX_RETRY_DELAY,
          )
          retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
        }

        setIsLoading(false) // Only set to false after successful fetch and processing
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          logger.warn("Failed to load prompts from API.", err)
          // Retry on error with exponential backoff
          const delay = Math.min(
            5000 * Math.pow(2, retryCount),
            MAX_RETRY_DELAY,
          )
          retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
        }
      } finally {
        setIsLoading(false)
      }
    }

    fetchPrompts()

    return () => {
      controller.abort()
      if (retryTimeoutId) clearTimeout(retryTimeoutId)
    }
  }, [pattern])

  const options = useMemo(() => {
    const rows = categories.flatMap((category) =>
      category.prompts.map((prompt) => ({
        category: category.name,
        prompt: String(prompt?.prompt ?? ""),
        description: String(prompt?.description ?? ""),
      })),
    )

    return rows
      .filter((row) => row.prompt.trim().length > 0)
      .map((row) => ({
        value: row.prompt,
        label: "",
        customElement: (
          <CustomDropdownListItemContent
            prompt={row.prompt}
            description={row.description}
          />
        ),
        menuItemTooltipProps: row.category
          ? { title: row.category.toUpperCase() }
          : undefined,
      }))
  }, [categories])

  const selected = options[0] ?? {
    label: "Suggested Prompts",
    value: "Suggested Prompts",
  }

  return (
    <Dropdown
      options={options}
      selected={selected}
      onChange={(opt) => {
        if (typeof opt?.value === "string" && opt.value.trim().length > 0) {
          onSelect(opt.value)
        }
      }}
      label="Suggested Prompts"
      showSelectedOption={false}
      buttonProps={{
        size: "small",
        disabled: isLoading || options.length === 0,
      }}
      fixedWidth
    />
  )
}

export default CoffeePromptsDropdown
