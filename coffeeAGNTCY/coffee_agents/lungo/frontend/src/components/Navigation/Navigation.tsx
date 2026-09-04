/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useEffect, useMemo, useState } from "react"
import MenuIcon from "@mui/icons-material/Menu"
import HelpOutline from "@mui/icons-material/HelpOutline"
import { Header, IconButton, Stack, Tooltip, Box } from "@open-ui-kit/core"

import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"
import { useAppThemeMode } from "@/hooks/useApp"
import type { SidebarProps } from "@/components/Sidebar/Sidebar"
import ThemeToggleIcon from "../icons/ThemeToggleIcon"
import CatalogNavigationDrawer, {
  CATALOG_NAV_DRAWER_ID,
} from "./CatalogNavigationDrawer"
import InfoDialog from "./InfoDialog"
import {
  navigationHeaderIconButtonSx,
  navigationHeaderSx,
} from "./navigationHeaderSx"

const CATALOG_MENU_BUTTON_LABEL = "Open workflow catalog"

interface NavigationProps {
  /** When set, shows a catalog menu trigger below the `sm` breakpoint. */
  catalogSidebarProps?: SidebarProps
}

const Navigation: React.FC<NavigationProps> = ({ catalogSidebarProps }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isCatalogMenuOpen, setIsCatalogMenuOpen] = useState(false)
  const { isDarkMode, toggleTheme } = useAppThemeMode()

  const showCatalogMenu = catalogSidebarProps !== undefined

  useEffect(() => {
    if (!showCatalogMenu) {
      setIsCatalogMenuOpen(false)
    }
  }, [showCatalogMenu])

  const handleHelpClick = useCallback(() => {
    setIsDialogOpen(true)
  }, [])

  const handleCloseDialog = useCallback(() => {
    setIsDialogOpen(false)
  }, [])

  const handleToggleCatalogMenu = useCallback(() => {
    setIsCatalogMenuOpen((prev) => !prev)
  }, [])

  const handleCloseCatalogMenu = useCallback(() => {
    setIsCatalogMenuOpen(false)
  }, [])

  const drawerSidebarProps = useMemo((): SidebarProps | undefined => {
    if (!catalogSidebarProps) {
      return undefined
    }

    const closeCatalogMenu = () => {
      setIsCatalogMenuOpen(false)
    }

    return {
      ...catalogSidebarProps,
      onSelectWorkflow: (summary) => {
        catalogSidebarProps.onSelectWorkflow(summary)
        closeCatalogMenu()
      },
      onSelectReferencePattern: catalogSidebarProps.onSelectReferencePattern
        ? (patternName) => {
            catalogSidebarProps.onSelectReferencePattern?.(patternName)
            closeCatalogMenu()
          }
        : undefined,
      onSelectPatternCategory: catalogSidebarProps.onSelectPatternCategory
        ? (categoryName) => {
            catalogSidebarProps.onSelectPatternCategory?.(categoryName)
            closeCatalogMenu()
          }
        : undefined,
    }
  }, [catalogSidebarProps])

  const themeToggleLabel = `Switch to ${isDarkMode ? "light" : "dark"} mode`

  return (
    <>
      <Header
        position="static"
        sx={(theme) => navigationHeaderSx(theme)}
        logo={
          <Stack direction="row" alignItems="center" spacing={2}>
            {showCatalogMenu ? (
              <Tooltip title={CATALOG_MENU_BUTTON_LABEL}>
                <Box component="span" sx={{ display: "inline-flex" }}>
                  <IconButton
                    aria-label={CATALOG_MENU_BUTTON_LABEL}
                    aria-controls={CATALOG_NAV_DRAWER_ID}
                    aria-expanded={isCatalogMenuOpen}
                    aria-haspopup="true"
                    onClick={handleToggleCatalogMenu}
                    sx={(theme) => navigationHeaderIconButtonSx(theme)}
                  >
                    <MenuIcon />
                  </IconButton>
                </Box>
              </Tooltip>
            ) : null}
            <Box
              component="img"
              src={coffeeAgntcyLogo}
              alt="Coffee AGNTCY Logo"
            />
          </Stack>
        }
        userSection={
          <Stack
            direction="row"
            sx={{
              gap: { xs: 0.5, sm: 1 },
            }}
          >
            <Tooltip title={themeToggleLabel}>
              <IconButton
                aria-label={themeToggleLabel}
                onClick={toggleTheme}
                sx={(theme) => navigationHeaderIconButtonSx(theme)}
              >
                <ThemeToggleIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Help">
              <IconButton
                aria-label="Help"
                onClick={handleHelpClick}
                sx={(theme) => navigationHeaderIconButtonSx(theme)}
              >
                <HelpOutline />
              </IconButton>
            </Tooltip>
          </Stack>
        }
      />

      {drawerSidebarProps ? (
        <CatalogNavigationDrawer
          open={isCatalogMenuOpen}
          onClose={handleCloseCatalogMenu}
          sidebarProps={drawerSidebarProps}
        />
      ) : null}

      <InfoDialog isOpen={isDialogOpen} onClose={handleCloseDialog} />
    </>
  )
}

export default Navigation
