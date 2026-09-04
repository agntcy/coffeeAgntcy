/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Themed drag handle between react-resizable-panels Panel siblings.
 */

import React from "react"
import { Separator } from "react-resizable-panels"
import { alpha, styled } from "@mui/material/styles"

import {
  RESIZABLE_PANEL_SEPARATOR_SIZE_PX,
  RESIZABLE_PANEL_SEPARATOR_TOUCH_PADDING_PX,
} from "./resizablePanelLayout"

export type ResizablePanelGroupOrientation = "horizontal" | "vertical"

export type ResizablePanelSeparatorProps = {
  id: string
  "aria-label": string
  orientation: ResizablePanelGroupOrientation
  disabled?: boolean
}

const StyledSeparator = styled(Separator, {
  shouldForwardProp: (prop) =>
    prop !== "resizeEnabled" && prop !== "orientation",
})<{
  orientation: ResizablePanelGroupOrientation
  resizeEnabled?: boolean
}>(({ theme, orientation, resizeEnabled = true }) => {
  const isLight = theme.palette.mode === "light"
  // B7: raise from 0.18/0.22 so the handle meets ≥3:1 UI contrast on paper.
  const restingOpacity = isLight ? 0.35 : 0.4
  const hoverOpacity = isLight ? 0.48 : 0.52
  const isHorizontalGroup = orientation === "horizontal"

  const touchPaddingPx = RESIZABLE_PANEL_SEPARATOR_TOUCH_PADDING_PX

  return {
    flexShrink: 0,
    position: "relative",
    zIndex: 1,
    boxSizing: "content-box",
    ...(isHorizontalGroup
      ? {
          width: RESIZABLE_PANEL_SEPARATOR_SIZE_PX,
          paddingLeft: touchPaddingPx,
          marginTop: 0,
          marginRight: 0,
          marginBottom: 0,
          marginLeft: -touchPaddingPx,
          backgroundClip: "content-box",
        }
      : {
          height: RESIZABLE_PANEL_SEPARATOR_SIZE_PX,
          paddingTop: touchPaddingPx,
          marginTop: -touchPaddingPx,
          marginRight: 0,
          marginBottom: 0,
          marginLeft: 0,
          backgroundClip: "content-box",
        }),
    border: 0,
    backgroundColor: alpha(theme.palette.text.primary, restingOpacity),
    cursor: resizeEnabled
      ? isHorizontalGroup
        ? "col-resize"
        : "row-resize"
      : "default",
    pointerEvents: resizeEnabled ? "auto" : "none",
    transition: theme.transitions.create("background-color", {
      duration: theme.transitions.duration.shortest,
    }),
    "&:hover": {
      backgroundClip: "border-box",
      backgroundColor: alpha(
        theme.palette.text.primary,
        resizeEnabled ? hoverOpacity : restingOpacity,
      ),
    },
    "&:focus-visible": {
      outline: `2px solid ${theme.palette.primary.main}`,
      outlineOffset: -2,
    },
  }
})

const ResizablePanelSeparator: React.FC<ResizablePanelSeparatorProps> = ({
  id,
  "aria-label": ariaLabel,
  orientation,
  disabled = false,
}) => (
  <StyledSeparator
    id={id}
    aria-label={ariaLabel}
    disabled={disabled}
    orientation={orientation}
    resizeEnabled={!disabled}
  />
)

export default ResizablePanelSeparator
