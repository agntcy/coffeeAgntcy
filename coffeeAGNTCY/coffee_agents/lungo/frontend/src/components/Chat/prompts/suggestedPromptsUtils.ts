/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { ReactNode } from "react"
import type { MenuProps } from "@mui/material/Menu"
import type { ButtonProps, TooltipProps } from "@open-ui-kit/core"
import type { DropdownOption } from "@/types/dropdownOption"
import type { GraphCanvasLayoutMetrics } from "@/contexts/graphCanvasLayout"
import type { PromptCategory } from "./PromptTypes"

export const SUGGESTED_PROMPTS_LABEL = "Suggested Prompts"

const PROMPTS_MENU_ANCHOR_GAP_PX = 8
const PROMPTS_MENU_VIEWPORT_MARGIN_PX = 16
const MAX_RETRY_DELAY_MS = 5000

export function parsePromptCategories(data: unknown): PromptCategory[] {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    return []
  }

  return Object.entries(data as Record<string, unknown>).map(
    ([name, value]) => ({
      name,
      prompts: Array.isArray(value) ? value : [],
    }),
  )
}

export function getRetryDelayMs(retryCount: number): number {
  return Math.min(5000 * 2 ** retryCount, MAX_RETRY_DELAY_MS)
}

export function categoriesToMenuOptions(
  categories: PromptCategory[],
  renderItem: (prompt: string, description: string) => ReactNode,
): DropdownOption<string>[] {
  return categories
    .flatMap((category) =>
      category.prompts.map((entry) => ({
        category: category.name,
        prompt: String(entry?.prompt ?? ""),
        description: String(entry?.description ?? ""),
      })),
    )
    .filter((row) => row.prompt.trim().length > 0)
    .map((row) => ({
      label: "",
      value: row.prompt,
      customElement: renderItem(row.prompt, row.description),
      menuItemTooltipProps: row.category
        ? { title: row.category.toUpperCase() }
        : undefined,
    }))
}

export function computePromptsMenuMaxWidth(
  triggerRect: Pick<DOMRectReadOnly, "left">,
  layout: GraphCanvasLayoutMetrics,
): number | undefined {
  const { graphCanvasWidth, mainContentLeft, mainContentWidth } = layout
  const candidates: number[] = []

  if (mainContentLeft !== undefined && mainContentWidth !== undefined) {
    const mainRight = mainContentLeft + mainContentWidth
    const availableFromTrigger =
      mainRight - triggerRect.left - PROMPTS_MENU_VIEWPORT_MARGIN_PX
    if (availableFromTrigger > 0) {
      candidates.push(availableFromTrigger)
    }
  }

  if (graphCanvasWidth !== undefined && graphCanvasWidth > 0) {
    candidates.push(graphCanvasWidth)
  }

  return candidates.length > 0 ? Math.floor(Math.min(...candidates)) : undefined
}

export function getPromptsMenuProps(menuMaxWidth?: number): Partial<MenuProps> {
  return {
    anchorOrigin: {
      vertical: -PROMPTS_MENU_ANCHOR_GAP_PX,
      horizontal: "left",
    },
    transformOrigin: {
      vertical: "bottom",
      horizontal: "left",
    },
    sx: { marginTop: 0 },
    slotProps: {
      paper: {
        sx: {
          ...(menuMaxWidth !== undefined ? { maxWidth: menuMaxWidth } : {}),
        },
      },
    },
  }
}

function isInactive(isLoading: boolean, optionCount: number): boolean {
  return isLoading || optionCount === 0
}

export function getPromptsTriggerButtonProps(
  isLoading: boolean,
  optionCount: number,
): ButtonProps {
  const base: ButtonProps = { size: "medium", variant: "primary" }

  if (!isInactive(isLoading, optionCount)) {
    return base
  }

  return {
    ...base,
    "aria-disabled": true,
    tabIndex: -1,
  }
}

export function getPromptsTriggerTooltipProps(
  isLoading: boolean,
  optionCount: number,
): Partial<TooltipProps> | undefined {
  if (isLoading) {
    return { title: "Loading prompts..." }
  }
  if (optionCount === 0) {
    return { title: "No prompts available" }
  }
  return undefined
}
