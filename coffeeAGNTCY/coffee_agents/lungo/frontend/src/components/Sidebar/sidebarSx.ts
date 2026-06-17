/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Theme } from "@mui/material/styles"

/**
 * Border radius for SidebarItem, SidebarDropdown, rail rows, and frame controls.
 */
export const sidebarBorderRadius = (theme: Theme) => theme.shape.borderRadius

/** Top margin for sidebar rows (`theme.spacing(1)` → 8px). */
export const sidebarItemMarginTop = (theme: Theme) => theme.spacing(1)

/** Width for catalog and rail ListItemButton rows (overrides theme default fixed width). */
export const sidebarListItemButtonSx = {
  width: "auto",
  maxWidth: "100%",
} as const

/**
 * Sidebar row buttons: neutral text with rounded fill emphasis on hover,
 * selection, focus, and active press.
 */
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
      "& .MuiTypography-root": {
        fontWeight: 600,
      },
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

/** Composed ListItemButton styles for catalog `SidebarItem` rows. */
export const sidebarItemButtonSx = (theme: Theme) => ({
  ...sidebarListItemButtonSx,
  ...sidebarRowButtonStateSx(theme),
})

/**
 * ListItem wrappers stay transparent; hover, focus, and selected styles belong on
 * the inner ListItemButton.
 */
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

/** Left padding for nested content in an expanded `SidebarDropdown` panel. */
export const sidebarDropdownPanelPaddingLeft = (theme: Theme) =>
  theme.spacing(1)
