/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import { IconButton, Tooltip } from "@open-ui-kit/core"
import HelpOutline from "@mui/icons-material/HelpOutline"
import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"
import ThemeToggleIcon from "../icons/ThemeToggleIcon"
import { useTheme } from "@/hooks/useTheme"
import InfoModal from "./InfoModal"

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

  const lightModeText = `Switch to ${isLightMode ? "dark" : "light"} mode`

  return (
    <div className="order-0 box-border flex h-[52px] w-full flex-none flex-grow-0 flex-col items-start self-stretch border-r border-nav-border p-0">
      <div className="order-0 box-border flex h-[52px] w-full flex-none flex-grow-0 flex-row items-center justify-between gap-2 self-stretch border-b border-nav-border px-2 py-[10px] sm:px-4">
        <div className="order-0 ml-2 flex h-[45px] w-32 flex-none flex-grow-0 flex-row items-center gap-2 p-0 opacity-100 sm:ml-4 sm:w-40">
          <div className="order-0 flex h-[45px] w-32 flex-none flex-grow-0 flex-row items-center gap-1 p-0 opacity-100 sm:w-40">
            <div className="order-0 flex h-[42px] w-auto flex-none flex-grow-0 items-center justify-center gap-0.5 opacity-100">
              <img
                src={coffeeAgntcyLogo}
                alt="Coffee AGNTCY Logo"
                className="h-full w-32 object-contain sm:w-40"
              />
            </div>
          </div>
        </div>

        <div className="order-3 flex flex-none flex-grow-0 flex-row items-center justify-end gap-2 p-0">
          <Tooltip title={lightModeText}>
            <IconButton
              aria-label={lightModeText}
              onClick={handleThemeToggle}
              size="small"
              color="inherit"
              sx={{
                order: 0,
                width: 32,
                height: 32,
                flex: "none",
                opacity: 1,
                "&:hover": { opacity: 0.8 },
              }}
            >
              <ThemeToggleIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Help">
            <IconButton
              aria-label="Help"
              onClick={handleHelpClick}
              size="small"
              color="inherit"
              sx={{
                order: 0,
                width: 32,
                height: 32,
                flex: "none",
                opacity: 1,
                "&:hover": { opacity: 0.8 },
              }}
            >
              <HelpOutline sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
        </div>
      </div>

      <InfoModal isOpen={isModalOpen} onClose={handleCloseModal} />
    </div>
  )
}

export default Navigation
