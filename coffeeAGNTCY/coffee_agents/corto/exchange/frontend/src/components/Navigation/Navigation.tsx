/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import { HelpCircle } from "lucide-react"
import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"
import InfoModal from "./InfoModal"

const Navigation: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isLightMode, setIsLightMode] = useState(false)

  const handleHelpClick = () => {
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
  }

  const handleThemeToggle = () => {
    setIsLightMode(!isLightMode)

    if (!isLightMode) {
      document.body.setAttribute("data-theme", "light")
    } else {
      document.body.removeAttribute("data-theme")
    }
  }
  return (
    <div className="order-0 border-nav-border bg-nav-background box-border flex h-[52px] w-full flex-none flex-grow-0 flex-col items-start self-stretch border-r p-0">
      <div className="order-0 border-nav-border bg-nav-background-secondary box-border flex h-[52px] w-full flex-none flex-grow-0 flex-row items-center justify-between gap-2 self-stretch border-b px-2 py-[10px] sm:px-4">
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
          <button
            className="order-0 flex h-8 w-8 flex-none flex-grow-0 items-center justify-center rounded p-1.5 transition-opacity hover:opacity-80"
            title={`Switch to ${isLightMode ? "dark" : "light"} mode`}
            onClick={handleThemeToggle}
          >
            <svg viewBox="0 0 24 24" className="text-nav-text h-5 w-5">
              <path
                fill="currentColor"
                d="M12,9c1.65,0,3,1.35,3,3s-1.35,3-3,3s-3-1.35-3-3S10.35,9,12,9 M12,7c-2.76,0-5,2.24-5,5s2.24,5,5,5s5-2.24,5-5 S14.76,7,12,7L12,7z M2,13l2,0c0.55,0,1-0.45,1-1s-0.45-1-1-1l-2,0c-0.55,0-1,0.45-1,1S1.45,13,2,13z M20,13l2,0c0.55,0,1-0.45,1-1 s-0.45-1-1-1l-2,0c-0.55,0-1,0.45-1,1S19.45,13,20,13z M11,2v2c0,0.55,0.45,1,1,1s1-0.45,1-1V2c0-0.55-0.45-1-1-1S11,1.45,11,2z M11,20v2c0,0.55,0.45,1,1,1s1-0.45,1-1v-2c0-0.55-0.45-1-1-1C11.45,19,11,19.45,11,20z M5.99,4.58c-0.39-0.39-1.03-0.39-1.41,0 c-0.39,0.39-0.39,1.03,0,1.41l1.06,1.06c0.39,0.39,1.03,0.39,1.41,0s0.39-1.03,0-1.41L5.99,4.58z M18.36,16.95 c-0.39-0.39-1.03-0.39-1.41,0c-0.39,0.39-0.39,1.03,0,1.41l1.06,1.06c0.39,0.39,1.03,0.39,1.41,0c0.39-0.39,0.39-1.03,0-1.41 L18.36,16.95z M19.42,5.99c0.39-0.39,0.39-1.03,0-1.41c-0.39-0.39-1.03-0.39-1.41,0l-1.06,1.06c-0.39,0.39-0.39,1.03,0,1.41 s1.03,0.39,1.41,0L19.42,5.99z M7.05,18.36c0.39-0.39,0.39-1.03,0-1.41c-0.39-0.39-1.03-0.39-1.41,0l-1.06,1.06 c-0.39,0.39-0.39,1.03,0,1.41s1.03,0.39,1.41,0L7.05,18.36z"
              />
            </svg>
          </button>
          <button
            className="order-0 flex h-8 w-8 flex-none flex-grow-0 items-center justify-center rounded p-1.5 transition-opacity hover:opacity-80"
            title="Help"
            onClick={handleHelpClick}
          >
            <HelpCircle className="text-nav-text h-5 w-5" />
          </button>
        </div>
      </div>

      <InfoModal isOpen={isModalOpen} onClose={handleCloseModal} />
    </div>
  )
}

export default Navigation
