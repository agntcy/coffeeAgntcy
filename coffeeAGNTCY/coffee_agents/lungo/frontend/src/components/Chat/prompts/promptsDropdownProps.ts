/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Dropdown from @open-ui-kit/core wraps its trigger in Tooltip; a disabled
 * button does not receive pointer events. Use aria-disabled + pointer-events
 * instead of the native disabled attribute while loading or empty.
 */

import { createElement } from "react"
import KeyboardArrowDown from "@mui/icons-material/KeyboardArrowDown"
import type { TooltipProps } from "@open-ui-kit/core"
import type { ButtonProps } from "@mui/material/Button"

export const promptsDropdownEndIcon = createElement(KeyboardArrowDown, {
  //fontSize: "small",
  //"aria-hidden": true,
})

export function isPromptsDropdownInactive(
  isLoading: boolean,
  optionCount: number,
): boolean {
  return isLoading || optionCount === 0
}

export function getPromptsDropdownButtonProps(
  isLoading: boolean,
  optionCount: number,
): ButtonProps {
  const base: ButtonProps = { size: "medium", variant: "outlined" }

  if (!isPromptsDropdownInactive(isLoading, optionCount)) {
    return base
  }

  return {
    ...base,
    "aria-disabled": true,
    tabIndex: -1,
    sx: { opacity: 0.5, pointerEvents: "none" },
  }
}

export function getPromptsDropdownButtonTooltipProps(
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
