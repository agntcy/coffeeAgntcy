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

const DEFAULT_LOGISTICS_APP_API_URL = "http://127.0.0.1:9090"
const LOGISTICS_APP_API_URL =
  env.get("VITE_LOGISTICS_APP_API_URL") || DEFAULT_LOGISTICS_APP_API_URL

interface LogisticsPromptsDropdownProps {
  visible: boolean
  onSelect: (query: string) => void
}

const LogisticsPromptsDropdown: React.FC<LogisticsPromptsDropdownProps> = ({
  visible,
  onSelect,
}) => {
  const [isLoading, setIsLoading] = useState(true)
  const [categories, setCategories] = useState<PromptCategory[]>([])

  // Fetch prompts on mount
  useEffect(() => {
    const controller = new AbortController()
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null
    const MAX_RETRY_DELAY = 5000 // 5 seconds max

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        const res = await fetch(`${LOGISTICS_APP_API_URL}/suggested-prompts`, {
          cache: "no-cache",
          signal: controller.signal,
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data: unknown = await res.json()

        if (data && typeof data === "object") {
          const categories = Object.entries(data).map(([key, value]) => ({
            name: key,
            prompts: Array.isArray(value) ? value : [],
          }))
          setCategories(categories)

          // Retry if all categories are empty
          if (categories.every((category) => category.prompts.length === 0)) {
            const delay = Math.min(
              5000 * Math.pow(2, retryCount),
              MAX_RETRY_DELAY,
            )
            retryTimeoutId = setTimeout(
              () => fetchPrompts(retryCount + 1),
              delay,
            )
          }
        }

        setIsLoading(false)
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          logger.warn("Failed to load logistics prompts from API.", err)
          // Retry on error with exponential backoff
          const delay = Math.min(
            5000 * Math.pow(2, retryCount),
            MAX_RETRY_DELAY,
          )
          retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
        }
      }
    }

    fetchPrompts()

    return () => {
      controller.abort()
      if (retryTimeoutId) clearTimeout(retryTimeoutId)
    }
  }, [])

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
        label: "",
        value: row.prompt,
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

  if (!visible) return null

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

export default LogisticsPromptsDropdown
