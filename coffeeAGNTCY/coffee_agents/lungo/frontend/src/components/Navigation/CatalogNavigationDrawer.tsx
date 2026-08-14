/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Mobile workflow catalog: full-area panel below the top nav bar (toggle stays visible).
 */

import React, { useEffect } from "react"
import { Box, Typography } from "@open-ui-kit/core"

import Sidebar, { type SidebarProps } from "@/components/Sidebar/Sidebar"
import { getAppShellBackgroundColor } from "@/components/MainArea/mainAreaBackground"
import {
  LUNGO_NAV_HEADER_HEIGHT_PX,
} from "./navigationHeaderSx"

/** Matches panel root id for `aria-controls` on the nav menu trigger. */
export const CATALOG_NAV_DRAWER_ID = "catalog-navigation-drawer"

/** Inset padding for the catalog panel (includes 32px on the right). */
const CATALOG_MENU_BOX_PADDING_PX = 32

export type CatalogNavigationDrawerProps = {
  open: boolean
  onClose: () => void
  sidebarProps: SidebarProps
}

const CatalogNavigationDrawer: React.FC<CatalogNavigationDrawerProps> = ({
  open,
  onClose,
  sidebarProps,
}) => {
  useEffect(() => {
    if (!open) {
      return undefined
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose()
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => {
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [open, onClose])

  if (!open) {
    return null
  }

  return (
    <Box
      id={CATALOG_NAV_DRAWER_ID}
      component="nav"
      role="dialog"
      aria-modal="false"
      aria-label="Workflow catalog"
      sx={(theme) => ({
        position: "fixed",
        top: LUNGO_NAV_HEADER_HEIGHT_PX,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: theme.zIndex.appBar - 1,
        boxSizing: "border-box",
        width: "100%",
        height: `calc(100vh - ${LUNGO_NAV_HEADER_HEIGHT_PX}px)`,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        minWidth: 0,
        overflow: "hidden",
        bgcolor: getAppShellBackgroundColor(theme),
        p: `${CATALOG_MENU_BOX_PADDING_PX}px`,
      })}
    >
      <Typography variant="h6" sx={{ mb: 2, flexShrink: 0 }}>
        Agentic Patterns
      </Typography>
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          minWidth: 0,
          overflow: "auto",
        }}
      >
        <Sidebar {...sidebarProps} embeddedInDrawer showHeading={false} />
      </Box>
    </Box>
  )
}

export default CatalogNavigationDrawer
