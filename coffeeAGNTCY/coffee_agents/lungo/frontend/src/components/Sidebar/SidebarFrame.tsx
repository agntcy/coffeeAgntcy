/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Button, List } from "@mui/material"
import { Drawer } from "@open-ui-kit/core"
import type { CSSObject, SxProps, Theme } from "@mui/material/styles"
import { styled } from "@mui/material/styles"
import { Icons } from "@open-ui-kit/core"
import { SidebarRailRow } from "./SidebarRailRow"

/** Config for icon-rail entries rendered by the internal `renderListItem` helper. */
export interface SidebarRailItem {
  id: string
  "aria-label": string
  tooltip?: string
  icon?: React.ReactElement
  onClick?: () => void
  href?: string
  target?: string
  iconOnly?: boolean
  selected?: boolean
}

export interface SidebarFrameProps {
  navigationItems?: Array<SidebarRailItem | React.ReactElement>
  sx?: SxProps<Theme>
  collapsible?: boolean
  drawerWidth?: string
  initialOpen?: boolean
}

const openedMixin = (theme: Theme, width: string): CSSObject => ({
  width,
  transition: theme.transitions.create("width", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: "hidden",
  backgroundColor: "#EFF3FC",
  borderRadius: 0,
})

const closedMixin = (theme: Theme): CSSObject => ({
  transition: theme.transitions.create("width", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  overflowX: "hidden",
  backgroundColor: "#EFF3FC",
  borderRadius: 0,
  width: "5.5rem",
})

const StyledDrawer = styled(Drawer, {
  shouldForwardProp: (prop) => prop !== "open" && prop !== "drawerWidth",
})<{ drawerWidth: string; open?: boolean }>(({ theme, open, drawerWidth }) => ({
  width: drawerWidth,
  flexShrink: 0,
  whiteSpace: "nowrap",
  boxSizing: "border-box",
  "& .MuiDrawer-paper": {
    borderRadius: 0,
  },
  ...(open && {
    ...openedMixin(theme, drawerWidth),
    "& .MuiDrawer-paper": openedMixin(theme, drawerWidth),
  }),
  ...(!open && {
    ...closedMixin(theme),
    "& .MuiDrawer-paper": closedMixin(theme),
  }),
}))

/**
 * Renders one top-level rail entry: either a cloned custom slot (e.g. Lungo nav tree)
 * with `iconOnly`, or a compact icon + label row from {@link SidebarRailItem}.
 */
function renderListItem(
  item: SidebarRailItem | React.ReactElement,
  isOpen: boolean,
): React.ReactNode {
  if (React.isValidElement(item)) {
    return React.cloneElement(
      item as React.ReactElement<{ iconOnly?: boolean }>,
      {
        iconOnly: !isOpen,
      },
    )
  }

  const row = item as SidebarRailItem
  return (
    <SidebarRailRow
      id={row.id}
      aria-label={row["aria-label"]}
      tooltip={row.tooltip ?? ""}
      icon={row.icon}
      railOpen={isOpen}
      onClick={row.onClick}
      href={row.href}
      target={row.target}
      selected={row.selected}
    />
  )
}

export function SidebarFrame({
  navigationItems,
  drawerWidth = "16.5rem",
  initialOpen = true,
  sx,
}: SidebarFrameProps) {
  const [isOpen, setIsOpen] = React.useState(initialOpen)

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  return (
    <StyledDrawer
      variant="permanent"
      data-testid="sidebar"
      open={isOpen}
      drawerWidth={drawerWidth}
      slotProps={{
        paper: {
          sx: {
            position: "relative",
            display: "flex",
            flexDirection: "column",
            height: "100%",
            justifyContent: "space-between",
            paddingTop: "0px",
            paddingRight: "0px",
            ...sx,
          },
        },
      }}
    >
      <List
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: "24px",
          alignItems: "baseline",
          overflowY: "auto",
          padding: "24px",
          paddingLeft: "0px",
        }}
      >
        {navigationItems?.map((item, index) => {
          const key = React.isValidElement(item)
            ? String(item.key ?? `nav-${index}`)
            : (item as SidebarRailItem).id
          return (
            <React.Fragment key={key}>
              {renderListItem(item, isOpen)}
            </React.Fragment>
          )
        })}
      </List>
      <Button
        sx={{
          borderRadius: "4px",
          marginTop: "8px",
          padding: "8px",
          "&.MuiButtonBase-root": { ":focus": { outline: "none" } },
        }}
        variant="outlined"
        onClick={handleToggle}
      >
        {isOpen ? <Icons.KeyboardArrowLeft /> : <Icons.KeyboardArrowRight />}
      </Button>
    </StyledDrawer>
  )
}
