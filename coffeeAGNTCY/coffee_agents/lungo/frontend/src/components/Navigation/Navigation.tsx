/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useState } from "react"
import { Header, IconButton, Stack, Tooltip, Box } from "@open-ui-kit/core"
import HelpOutline from "@mui/icons-material/HelpOutline"

import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"
import { useAppThemeMode } from "@/hooks/useAppThemeMode"
import ThemeToggleIcon from "../icons/ThemeToggleIcon"
import InfoModal from "./InfoModal"
import {
  navigationHeaderIconButtonSx,
  navigationHeaderSx,
} from "./navigationHeaderSx"

const Navigation: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const { isDarkMode, toggleTheme } = useAppThemeMode()

  const handleHelpClick = useCallback(() => {
    setIsModalOpen(true)
  }, [setIsModalOpen])

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false)
  }, [setIsModalOpen])

  const themeToggleLabel = `Switch to ${isDarkMode ? "light" : "dark"} mode`

  return (
    <>
      <Header
        position="static"
        sx={navigationHeaderSx()}
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
                sx={navigationHeaderIconButtonSx()}
              >
                <ThemeToggleIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Help">
              <IconButton
                aria-label="Help"
                onClick={handleHelpClick}
                sx={navigationHeaderIconButtonSx()}
              >
                <HelpOutline />
              </IconButton>
            </Tooltip>
          </Stack>
        }
      />

      <InfoModal isOpen={isModalOpen} onClose={handleCloseModal} />
    </>
  )
}

export default Navigation
