/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Theme } from "@mui/material/styles"

export const sidebarBorderRadius = (theme: Theme) => theme.shape.borderRadius

export const sidebarItemMarginTop = (theme: Theme) => theme.spacing(1)

export const sidebarListItemButtonSx = {
  width: "auto",
  maxWidth: "100%",
} as const

export const sidebarRowButtonStateSx = (theme: Theme) => {
  const radius = sidebarBorderRadius(theme)
  const hoverFill = {
    bgcolor: theme.palette.action.hover,
    backgroundColor: theme.palette.action.hover,
  }
  const activeFill = {
    bgcolor: theme.palette.action.selected,
    backgroundColor: theme.palette.action.selected,
  }
  const surfaceTransition = theme.transitions.create(["background-color"], {
    duration: theme.transitions.duration.shortest,
  })

  return {
    color: theme.palette.text.primary,
    bgcolor: "transparent",
    backgroundColor: "transparent",
    borderRadius: radius,
    transition: surfaceTransition,
    "& .MuiTypography-root": {
      color: "inherit",
      fontWeight: 400,
    },
    "& .MuiSvgIcon-root": {
      color: "inherit",
    },
    "&:hover": {
      ...hoverFill,
      color: theme.palette.text.primary,
    },
    "&:active": {
      ...activeFill,
      color: theme.palette.text.primary,
    },
    "&.Mui-selected": {
      ...activeFill,
      color: theme.palette.text.primary,
    },
    "&.Mui-selected:hover": {
      ...hoverFill,
      color: theme.palette.text.primary,
    },
    "&.Mui-focusVisible": {
      ...hoverFill,
      outline: `2px solid ${theme.palette.divider}`,
      outlineOffset: 2,
    },
  }
}

export const sidebarItemButtonSx = (theme: Theme) => ({
  ...sidebarListItemButtonSx,
  ...sidebarRowButtonStateSx(theme),
})

export const sidebarListItemSx = () => ({
  backgroundColor: "transparent",
  "&:hover": {
    backgroundColor: "transparent",
  },
  "&:focus": {
    backgroundColor: "transparent",
  },
  "&:focus-within": {
    backgroundColor: "transparent",
  },
  "&.Mui-focusVisible": {
    backgroundColor: "transparent",
  },
  "&.Mui-selected": {
    backgroundColor: "transparent",
  },
})

export const sidebarRowTitleSx = {
  minWidth: 0,
  whiteSpace: "normal",
  overflowWrap: "anywhere",
  wordBreak: "break-word",
} as const
