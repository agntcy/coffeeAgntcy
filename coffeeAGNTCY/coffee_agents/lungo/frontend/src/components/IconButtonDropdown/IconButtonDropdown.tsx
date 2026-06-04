/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, {
  useCallback,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react"
import { Box, IconButton, Menu, Tooltip } from "@open-ui-kit/core"
import type { IconButtonProps, MenuProps } from "@mui/material"

export type IconButtonDropdownTrigger = {
  /** Icon rendered inside the `IconButton`. */
  icon: React.ReactNode
  iconButtonProps?: Omit<IconButtonProps, "children" | "onClick" | "aria-label">
}

export interface IconButtonDropdownProps {
  /** Accessible name for the trigger button. */
  ariaLabel: string
  /** Optional hover label for the trigger (e.g. graph identity menu). */
  tooltipTitle?: string
  /** Trigger rendered as an OUK `IconButton`. */
  trigger: IconButtonDropdownTrigger
  /**
   * Arbitrary dropdown content. This component does not impose a list/options structure.
   * The content is rendered inside the menu paper.
   */
  children: React.ReactNode
  /**
   * If true (default), clicking anywhere inside the dropdown closes it.
   * If false, the dropdown stays open unless closed via outside click / Esc / trigger click.
   */
  closeOnContentClick?: boolean
  /** Forwarded to the underlying menu for sizing/overflow/etc. Positioning defaults mirror OUK dropdown behavior. */
  menuProps?: Omit<
    MenuProps,
    "open" | "onClose" | "anchorEl" | "children" | "id"
  >
  /**
   * Controlled open state. When set, `onOpenChange` is called when the menu should open or close.
   * Use with `onOpenChange` for parents that need to sync (e.g. graph identity menu).
   */
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export const IconButtonDropdown: React.FC<IconButtonDropdownProps> = ({
  ariaLabel,
  tooltipTitle,
  trigger,
  children,
  closeOnContentClick = true,
  menuProps,
  open: openProp,
  onOpenChange,
}) => {
  const menuId = useId()
  const buttonRef = useRef<HTMLButtonElement | null>(null)
  const [uncontrolledAnchor, setUncontrolledAnchor] =
    useState<HTMLElement | null>(null)

  const isControlled = openProp !== undefined
  const openControlled = Boolean(openProp)

  const setAnchorFromRef = useCallback(() => {
    if (buttonRef.current) setUncontrolledAnchor(buttonRef.current)
  }, [])

  useLayoutEffect(() => {
    if (!isControlled) return
    if (openControlled) setAnchorFromRef()
    else setUncontrolledAnchor(null)
  }, [isControlled, openControlled, setAnchorFromRef])

  const anchorEl = isControlled ? uncontrolledAnchor : uncontrolledAnchor
  const menuOpen = Boolean(anchorEl)

  const handleUncontrolledOpen = useCallback(
    (event: React.MouseEvent<HTMLElement>) => {
      setUncontrolledAnchor(event.currentTarget)
    },
    [],
  )

  const handleClose = useCallback(() => {
    if (isControlled) {
      onOpenChange?.(false)
    } else {
      setUncontrolledAnchor(null)
    }
  }, [isControlled, onOpenChange])

  const handleTriggerClick = useCallback(
    (event: React.MouseEvent<HTMLElement>) => {
      if (isControlled) {
        onOpenChange?.(!openControlled)
      } else {
        handleUncontrolledOpen(event)
      }
    },
    [handleUncontrolledOpen, isControlled, onOpenChange, openControlled],
  )

  const triggerButton = (
    <IconButton
      ref={buttonRef}
      aria-label={ariaLabel}
      aria-controls={menuOpen ? menuId : undefined}
      aria-haspopup="menu"
      aria-expanded={menuOpen ? "true" : undefined}
      onClick={handleTriggerClick}
      {...trigger.iconButtonProps}
    >
      {trigger.icon}
    </IconButton>
  )

  return (
    <>
      {tooltipTitle ? (
        <Tooltip title={tooltipTitle} placement="left" arrow>
          <Box component="span" sx={{ display: "inline-flex" }}>
            {triggerButton}
          </Box>
        </Tooltip>
      ) : (
        triggerButton
      )}
      <Menu
        id={menuId}
        anchorEl={anchorEl}
        open={menuOpen}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        transformOrigin={{ vertical: "top", horizontal: "left" }}
        {...menuProps}
      >
        <Box
          onClick={() => {
            if (closeOnContentClick) handleClose()
          }}
        >
          {children}
        </Box>
      </Menu>
    </>
  )
}
