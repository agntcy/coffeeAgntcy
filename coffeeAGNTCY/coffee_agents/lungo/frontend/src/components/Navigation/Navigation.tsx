/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import { HelpCircle } from "lucide-react"
import type { SxProps, Theme } from "@mui/material/styles"
import { Header, IconButton, Stack, Tooltip, Box } from "@open-ui-kit/core"
import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"
import ThemeToggleIcon from "../icons/ThemeToggleIcon"
import { useTheme } from "@/hooks/useTheme"
import InfoModal from "./InfoModal"

const navIconButtonSx: SxProps<Theme> = () => ({
  "&:hover": {
    opacity: 0.85,
    backgroundColor: "transparent",
  },
})

const Navigation: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const { isLightMode, toggleTheme } = useTheme()

  const handleHelpClick = () => {
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
  }

  const handleThemeToggle = () => {
    toggleTheme()
  }

  const themeToggleLabel = `Switch to ${isLightMode ? "dark" : "light"} mode`

  return (
    <>
      <Header
        position="static"
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
                onClick={handleThemeToggle}
                size="small"
                sx={navIconButtonSx}
              >
                <ThemeToggleIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Help">
              <IconButton
                aria-label="Help"
                onClick={handleHelpClick}
                size="small"
                sx={navIconButtonSx}
              >
                <HelpCircle />
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
