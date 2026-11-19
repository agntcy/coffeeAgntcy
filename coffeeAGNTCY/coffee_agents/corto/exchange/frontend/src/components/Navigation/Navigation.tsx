/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useState } from "react"
import {
  Box,
  Header,
  IconButton,
  Icons,
  Stack,
  Tooltip,
} from "@open-ui-kit/core"

import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"
import type { SidebarProps } from "@/components/Sidebar/Sidebar"
import ThemeMenu from "./ThemeMenu"
import CatalogNavigationDrawer, {
  CATALOG_NAV_DRAWER_ID,
} from "./CatalogNavigationDrawer"
import InfoModal from "./InfoModal"
import {
  navigationHeaderIconButtonSx,
  navigationHeaderSx,
} from "./navigationHeaderSx"

const CATALOG_MENU_BUTTON_LABEL = "Open conversation catalog"

interface NavigationProps {
  /** When set, shows a catalog menu trigger below the `sm` breakpoint. */
  catalogSidebarProps?: SidebarProps
}

const Navigation: React.FC<NavigationProps> = ({ catalogSidebarProps }) => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isCatalogMenuOpen, setIsCatalogMenuOpen] = useState(false)
  const showCatalogMenu = catalogSidebarProps !== undefined
  const [catalogMenuAvailable, setCatalogMenuAvailable] =
    useState(showCatalogMenu)
  if (showCatalogMenu !== catalogMenuAvailable) {
    setCatalogMenuAvailable(showCatalogMenu)
    if (!showCatalogMenu) setIsCatalogMenuOpen(false)
  }

  const handleHelpClick = useCallback(() => {
    setIsModalOpen(true)
  }, [])

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false)
  }, [])

  const handleToggleCatalogMenu = useCallback(() => {
    setIsCatalogMenuOpen((prev) => !prev)
  }, [])

  const handleCloseCatalogMenu = useCallback(() => {
    setIsCatalogMenuOpen(false)
  }, [])

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
                    <Icons.Menu />
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
            <ThemeMenu />
            <Tooltip title="Help">
              <IconButton
                aria-label="Help"
                onClick={handleHelpClick}
                sx={(theme) => navigationHeaderIconButtonSx(theme)}
              >
                <Icons.QuestionCircleOutline />
              </IconButton>
            </Tooltip>
          </Stack>
        }
      />

      {showCatalogMenu ? (
        <CatalogNavigationDrawer
          open={isCatalogMenuOpen}
          onClose={handleCloseCatalogMenu}
          sidebarProps={catalogSidebarProps}
        />
      ) : null}

      <InfoModal isOpen={isModalOpen} onClose={handleCloseModal} />
    </>
  )
}

export default Navigation
