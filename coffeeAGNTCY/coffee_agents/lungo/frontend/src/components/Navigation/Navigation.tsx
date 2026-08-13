/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useState } from "react"
import { Header, IconButton, Stack, Tooltip, Box } from "@open-ui-kit/core"
import HelpOutline from "@mui/icons-material/HelpOutline"

import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"
import { useAppThemeMode } from "@/hooks/useApp"
import ThemeToggleIcon from "../icons/ThemeToggleIcon"
import InfoDialog from "./InfoDialog"
import {
  navigationHeaderIconButtonSx,
  navigationHeaderSx,
} from "./navigationHeaderSx"

const Navigation: React.FC = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const { isDarkMode, toggleTheme } = useAppThemeMode()

  const handleHelpClick = useCallback(() => {
    setIsDialogOpen(true)
  }, [setIsDialogOpen])

  const handleCloseDialog = useCallback(() => {
    setIsDialogOpen(false)
  }, [setIsDialogOpen])

  const themeToggleLabel = `Switch to ${isDarkMode ? "light" : "dark"} mode`

  return (
    <>
      <Header
        position="static"
        sx={(theme) => navigationHeaderSx(theme)}
        logo={
          <Box
            component="img"
            src={coffeeAgntcyLogo}
            alt="Coffee AGNTCY Logo"
          />
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

      <InfoDialog isOpen={isDialogOpen} onClose={handleCloseDialog} />
    </>
  )
}

export default Navigation
