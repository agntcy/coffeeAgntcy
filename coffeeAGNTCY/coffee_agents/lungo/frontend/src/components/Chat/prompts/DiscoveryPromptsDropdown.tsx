/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useMemo, useState } from "react"
import { Dropdown } from "@open-ui-kit/core"
import { getDiscoveryAppApiUrl, joinBaseUrl, LUNGO_FRONTEND_URLS } from "@/urls"
import { CustomDropdownListItemContent } from "./CustomDropdownListItemContent"
import { PromptCategory, Prompt } from "./PromptTypes"

interface DiscoveryPromptsDropdownProps {
  onSelect: (query: string) => void
}

const DiscoveryPromptsDropdown: React.FC<DiscoveryPromptsDropdownProps> = ({
  onSelect,
}) => {
  const [isLoading, setIsLoading] = useState(true)
  const [categories, setCategories] = useState<PromptCategory[]>([])

  useEffect(() => {
    const controller = new AbortController()
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null
    const MAX_RETRY_DELAY = 5000

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        const res = await fetch(
          joinBaseUrl(
            getDiscoveryAppApiUrl(),
            LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts,
          ),
          {
            cache: "no-cache",
            signal: controller.signal,
          },
        )

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data: unknown = await res.json()

        if (data && typeof data === "object") {
          const nextCategories = Object.entries(
            data as Record<string, unknown>,
          ).map(([key, value]) => ({
            name: key,
            prompts: Array.isArray(value) ? (value as Prompt[]) : [],
          }))

          setCategories(nextCategories)

          if (
            nextCategories.every((category) => category.prompts.length === 0)
          ) {
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
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
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
  }, [])

  const options = useMemo(() => {
    const rows = categories.flatMap((category) =>
      category.prompts.map((prompt) => ({
        category: category.name,
        prompt: String((prompt as Prompt)?.prompt ?? ""),
        description: String((prompt as Prompt)?.description ?? ""),
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

export default DiscoveryPromptsDropdown
