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
 * OUK `baseBackgroundWeak` — `#fbfcfe` in light mode (`theme.palette.vars`).
 * Used on `SidebarDropdown` `ListItem` roots only.
 */
export const sidebarDropdownListItemBackground = (theme: Theme) =>
  theme.palette.vars.baseBackgroundWeak

/**
 * ListItem wrappers stay transparent; hover, focus, and selected styles belong on
 * the inner ListItemButton.
 */
export const sidebarListItemSx = (theme: Theme) => ({
  paddingRight: theme.spacing(0.625),
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

/** `.MuiListItem-root` surface for `SidebarDropdown` at every tree level. */
export const sidebarDropdownListItemSx = {
  bgcolor: sidebarDropdownListItemBackground,
  borderRadius: sidebarBorderRadius,
  overflow: "hidden",
  "&:hover": {
    bgcolor: sidebarDropdownListItemBackground,
  },
  "&:focus": {
    bgcolor: sidebarDropdownListItemBackground,
  },
  "&:focus-within": {
    bgcolor: sidebarDropdownListItemBackground,
  },
  "&.Mui-focusVisible": {
    bgcolor: sidebarDropdownListItemBackground,
  },
  "&.Mui-selected": {
    bgcolor: sidebarDropdownListItemBackground,
  },
} as const

/**
 * Same fill as `.MuiListItemButton-root:hover` (theme `action.hover` token).
 */
export const sidebarListItemButtonHoverBackgroundSx = {
  bgcolor: sidebarDropdownListItemBackground,
  "&:hover": {
    bgcolor: "action.hover",
  },
  "&.Mui-focusVisible": {
    bgcolor: "action.hover",
  },
} as const

const sidebarDropdownCornerRadiiSx = (theme: Theme) => {
  const radius = sidebarBorderRadius(theme)
  return {
    borderRadius: radius,
    borderTopLeftRadius: radius,
    borderTopRightRadius: radius,
    borderBottomLeftRadius: radius,
    borderBottomRightRadius: radius,
  }
}

const sidebarDropdownExpandedTopCornersSx = (theme: Theme) => ({
  ...sidebarDropdownCornerRadiiSx(theme),
  borderBottomLeftRadius: 0,
  borderBottomRightRadius: 0,
})

const sidebarDropdownExpandedBottomCornersSx = (theme: Theme) => ({
  ...sidebarDropdownCornerRadiiSx(theme),
  borderTopLeftRadius: 0,
  borderTopRightRadius: 0,
})

/** ListItemButton radius for collapsed dropdown toggles. */
export const sidebarDropdownToggleSx = {
  borderRadius: sidebarBorderRadius,
} as const

/** Expanded dropdown toggle: fill + top corners (same radius token). */
export const sidebarDropdownToggleExpandedSx = (theme: Theme) => {
  const corners = sidebarDropdownExpandedTopCornersSx(theme)
  return {
    ...sidebarListItemButtonHoverBackgroundSx,
    ...corners,
    "&:hover": {
      ...sidebarListItemButtonHoverBackgroundSx["&:hover"],
      ...corners,
    },
    "&.Mui-focusVisible": {
      ...sidebarListItemButtonHoverBackgroundSx["&.Mui-focusVisible"],
      ...corners,
    },
  }
}

/** Left padding for nested content in an expanded `SidebarDropdown` panel. */
export const sidebarDropdownPanelPaddingLeft = (theme: Theme) =>
  theme.spacing(1)

/** Expanded dropdown panel: nested indent + bottom corners (same radius token). */
export const sidebarDropdownPanelExpandedSx = (theme: Theme) => {
  const corners = sidebarDropdownExpandedBottomCornersSx(theme)
  return {
    pl: sidebarDropdownPanelPaddingLeft(theme),
    ...sidebarListItemButtonHoverBackgroundSx,
    ...corners,
  }
}
