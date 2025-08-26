/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useRef, useEffect } from "react"

interface CoffeeGraderDropdownProps {
  visible: boolean
  onSelect: (query: string) => void
}

const CoffeeGraderDropdown: React.FC<CoffeeGraderDropdownProps> = ({
  visible,
  onSelect,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const dropdownItems = [
    "What are the flavor profiles of Ethiopian coffee?",
    "What does coffee harvested in Colombia in the summer taste like",
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
  }, [isOpen, visible])

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  const handleItemClick = (item: string) => {
    onSelect(item)
    setIsOpen(false)
  }

  if (!visible) {
    return null
  }

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      <div
        className={`bg-chat-background hover:bg-chat-background-hover flex h-9 w-166 cursor-pointer flex-row items-center gap-1 rounded-lg p-2 transition-colors duration-200 ease-in-out ${isOpen ? "bg-chat-background-hover" : ""} `}
        onClick={handleToggle}
      >
        <div className="order-0 flex h-5 w-122 flex-none flex-grow-0 flex-col items-start gap-1 p-0">
          <div className="order-0 text-chat-text h-5 w-122 flex-none flex-grow-0 self-stretch whitespace-nowrap font-cisco text-sm font-normal leading-5">
            Suggested Prompts
          </div>
        </div>
        <div className="relative order-1 h-6 w-6 flex-none flex-grow-0">
          <div
            className={`bg-node-icon-background absolute bottom-[36.35%] left-[26.77%] right-[26.77%] top-[36.35%] transition-transform duration-300 ease-in-out ${isOpen ? "rotate-180" : ""} `}
            style={{ clipPath: "polygon(50% 100%, 0% 0%, 100% 0%)" }}
          ></div>
        </div>
      </div>

      <div
        className={`border-nav-border bg-chat-dropdown-background absolute bottom-full left-0 z-[1000] mb-1 max-h-28 w-269 overflow-y-auto rounded-md border p-0.5 shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] ${isOpen ? "block animate-fadeInDropdown" : "hidden"} `}
      >
        {dropdownItems.map((item, index) => (
          <div
            key={index}
            className="bg-chat-dropdown-background hover:bg-chat-background-hover mx-0.5 my-0.5 flex min-h-10 w-[calc(100%-4px)] cursor-pointer items-center rounded px-2 py-[6px] transition-colors duration-200 ease-in-out"
            onClick={() => handleItemClick(item)}
          >
            <div className="w-full break-words font-inter text-sm font-normal leading-5 tracking-[0%] text-white">
              {item}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default CoffeeGraderDropdown
