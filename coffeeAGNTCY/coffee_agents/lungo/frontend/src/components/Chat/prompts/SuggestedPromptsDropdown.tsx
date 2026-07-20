/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Suggested Prompts dropdown for the chat composer (fetch + menu).
 */

import React, { useCallback, useMemo, useState } from "react"
import KeyboardArrowDown from "@mui/icons-material/KeyboardArrowDown"
import type { SxProps, Theme } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"
import {
  Box,
  Button,
  EmptyState,
  GeneralSize,
  Menu,
  MenuItem,
  Tooltip,
} from "@open-ui-kit/core"
import type { DropdownOption } from "@/types/dropdownOption"
import type { HttpRequestTarget } from "@/urls"
import { useGraphCanvasLayout } from "@/contexts/graphCanvasLayout"
import {
  computePromptsMenuMaxWidth,
  categoriesToMenuOptions,
  getPromptsMenuProps,
  getPromptsTriggerButtonProps,
  getPromptsTriggerTooltipProps,
  SUGGESTED_PROMPTS_LABEL,
} from "./suggestedPromptsUtils"
import { CustomDropdownListItemContent } from "./CustomDropdownListItemContent"
import { useSuggestedPrompts } from "./useSuggestedPrompts"

interface PromptMenuItemProps {
  option: DropdownOption<string>
  itemKey: string
  onSelect: (value: string) => void
  onClose: () => void
}

function PromptMenuItem({
  option,
  itemKey,
  onSelect,
  onClose,
}: PromptMenuItemProps) {
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    if (typeof option.value === "string" && option.value.trim()) {
      onSelect(option.value)
    }
    onClose()
    event.stopPropagation()
  }

  const menuItem = (
    <MenuItem
      onClick={handleClick}
      sx={{ whiteSpace: "normal", alignItems: "flex-start", py: 1 }}
    >
      {option.customElement ?? <span>{option.label || option.value}</span>}
    </MenuItem>
  )

  if (!option.menuItemTooltipProps?.title) {
    return React.cloneElement(menuItem, { key: itemKey })
  }

  return (
    <Tooltip
      key={itemKey}
      title={option.menuItemTooltipProps.title}
      {...option.menuItemTooltipProps}
      arrow
    >
      {menuItem}
    </Tooltip>
  )
}

export interface SuggestedPromptsDropdownProps {
  promptsRequest: HttpRequestTarget | null | undefined
  onSelect: (query: string) => void
  sx?: SxProps<Theme>
}

const SuggestedPromptsDropdown: React.FC<SuggestedPromptsDropdownProps> = ({
  promptsRequest,
  onSelect,
  sx,
}) => {
  const layout = useGraphCanvasLayout()
  const { categories, isLoading, isUnavailable } =
    useSuggestedPrompts(promptsRequest)
  const options = useMemo(
    () =>
      categoriesToMenuOptions(categories, (prompt, description) => (
        <CustomDropdownListItemContent
          prompt={prompt}
          description={description}
        />
      )),
    [categories],
  )
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const [menuMaxWidth, setMenuMaxWidth] = useState<number>()
  const open = Boolean(anchorEl)

  const handleOpen = useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      const triggerRect = event.currentTarget.getBoundingClientRect()
      setMenuMaxWidth(computePromptsMenuMaxWidth(triggerRect, layout))
      setAnchorEl(event.currentTarget)
      event.stopPropagation()
    },
    [layout],
  )

  const handleClose = useCallback(() => {
    setAnchorEl(null)
  }, [])

  const buttonProps = getPromptsTriggerButtonProps(
    isLoading,
    options.length,
    isUnavailable,
  )
  const isInactive = !isUnavailable && (isLoading || options.length === 0)
  const buttonTooltipProps = getPromptsTriggerTooltipProps(
    isLoading,
    options.length,
    isUnavailable,
  )
  const menuProps = useMemo(
    () => getPromptsMenuProps(menuMaxWidth),
    [menuMaxWidth],
  )

  const triggerButton = (
    <Button
      {...buttonProps}
      variant="primary"
      aria-haspopup="menu"
      aria-expanded={open ? "true" : undefined}
      onClick={handleOpen}
      sx={(theme): SystemStyleObject<Theme> => {
        const callerSx = typeof sx === "function" ? sx(theme) : sx
        const resolvedCallerSx = (
          Array.isArray(callerSx) ? {} : (callerSx ?? {})
        ) as SystemStyleObject<Theme>
        return {
          ...resolvedCallerSx,
          ...(isInactive ? { opacity: 0.5, pointerEvents: "none" } : {}),
        }
      }}
      endIcon={
        <KeyboardArrowDown
          aria-hidden
          sx={{
            transition: (theme) =>
              theme.transitions.create("transform", {
                duration: theme.transitions.duration.shortest,
              }),
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
          }}
        />
      }
    >
      {SUGGESTED_PROMPTS_LABEL}
    </Button>
  )

  return (
    <>
      {buttonTooltipProps?.title ? (
        <Tooltip title={buttonTooltipProps.title} {...buttonTooltipProps} arrow>
          <Box component="span" sx={{ display: "inline-flex" }}>
            {triggerButton}
          </Box>
        </Tooltip>
      ) : (
        triggerButton
      )}
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        {...menuProps}
      >
        {isUnavailable ? (
          <Box sx={{ p: 2, maxWidth: menuMaxWidth ?? 360 }}>
            <EmptyState
              variant="warning"
              hideIllustration
              size={GeneralSize.Small}
              title="Prompts unavailable"
              description="Suggested prompts could not be loaded. You can still type your own message."
            />
          </Box>
        ) : (
          options.map((option, index) => (
            <PromptMenuItem
              key={`${option.value}-${index}`}
              itemKey={`${option.value}-${index}`}
              option={option}
              onSelect={onSelect}
              onClose={handleClose}
            />
          ))
        )}
      </Menu>
    </>
  )
}

export default SuggestedPromptsDropdown
