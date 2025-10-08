/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useRef, useEffect } from "react"

interface LogisticsPromptsDropdownProps {
  visible: boolean
  onSelect: (query: string) => void
}

const LogisticsPromptsDropdown: React.FC<LogisticsPromptsDropdownProps> = ({
  visible,
  onSelect,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const logisticsPrompts = [
    "I want to order coffee $3.50 per pound for 500 lbs of coffee from the Tatooine farm",
  ]

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node

      if (
        isOpen &&
        dropdownRef.current &&
        !dropdownRef.current.contains(target)
      ) {
        setIsOpen(false)
      }
    }

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false)
      }
    }

    if (visible && isOpen) {
      document.addEventListener("mousedown", handleClickOutside, true)
      document.addEventListener("keydown", handleEscapeKey)
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside, true)
      document.removeEventListener("keydown", handleEscapeKey)
    }
  }, [visible, isOpen])

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  const handleItemClick = (prompt: string) => {
    onSelect(prompt)
    setIsOpen(false)
  }

  if (!visible) {
    return null
  }

  return (
    <div className="flex items-center gap-3">
      <div className="relative inline-block" ref={dropdownRef}>
        <div
          className={`flex h-9 w-166 cursor-pointer flex-row items-center gap-1 rounded-lg bg-chat-background p-2 transition-colors duration-200 ease-in-out hover:bg-chat-background-hover ${isOpen ? "bg-chat-background-hover" : ""} `}
          onClick={handleToggle}
        >
          <div className="order-0 flex h-5 w-122 flex-none flex-grow-0 flex-col items-start gap-1 p-0">
            <div className="order-0 h-5 w-122 flex-none flex-grow-0 self-stretch whitespace-nowrap font-cisco text-sm font-normal leading-5 text-chat-text">
              Suggested Prompts
            </div>
          </div>
          <div className="relative order-1 h-6 w-6 flex-none flex-grow-0">
            <div
              className={`absolute bottom-[36.35%] left-[26.77%] right-[26.77%] top-[36.35%] bg-chat-dropdown-icon transition-transform duration-300 ease-in-out ${isOpen ? "rotate-180" : ""} `}
              style={{ clipPath: "polygon(50% 100%, 0% 0%, 100% 0%)" }}
            ></div>
          </div>
        </div>

        <div
          className={`absolute bottom-full left-0 z-[1000] mb-1 w-269 overflow-y-auto rounded-[6px] border border-nav-border bg-chat-dropdown-background px-[2px] py-0 opacity-100 shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] ${isOpen ? "block animate-fadeInDropdown" : "hidden"} `}
        >
          <div className="px-2 py-2">
            <div className="mb-2 h-[36px] w-[265px] gap-2 bg-chat-dropdown-background pb-2 pl-[10px] pr-[10px] pt-2 font-inter text-sm font-normal leading-5 tracking-[0%] text-chat-text opacity-60">
              BUYER
            </div>
            {logisticsPrompts.map((item, index) => (
              <div
                key={`buyer-${index}`}
                className="mx-0.5 my-0.5 flex min-h-10 w-[calc(100%-4px)] cursor-pointer items-center rounded bg-chat-dropdown-background px-2 py-[6px] transition-colors duration-200 ease-in-out hover:bg-chat-background-hover"
                onClick={() => handleItemClick(item)}
              >
                <div className="w-full break-words font-cisco text-sm font-normal leading-5 tracking-[0%] text-chat-text">
                  {item}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default LogisticsPromptsDropdown
