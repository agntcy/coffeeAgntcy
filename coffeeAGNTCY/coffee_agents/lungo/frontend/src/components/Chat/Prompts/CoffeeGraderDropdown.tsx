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
    "Where can I get the best coffee with flavors like Ethiopian?",
  ]

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen])

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
        className={`flex h-9 w-166 cursor-pointer flex-row items-center gap-1 rounded-lg bg-[#1A2432] p-2 transition-colors duration-200 ease-in-out hover:bg-[#1F2A3A] ${isOpen ? "bg-[#1F2A3A]" : ""} `}
        onClick={handleToggle}
      >
        <div className="order-0 flex h-5 w-122 flex-none flex-grow-0 flex-col items-start gap-1 p-0">
          <div className="order-0 h-5 w-122 flex-none flex-grow-0 self-stretch whitespace-nowrap font-cisco text-sm font-normal leading-5 text-[#FBFCFE]">
            Suggested Prompts
          </div>
        </div>
        <div className="relative order-1 h-6 w-6 flex-none flex-grow-0">
          <div
            className={`absolute bottom-[36.35%] left-[26.77%] right-[26.77%] top-[36.35%] bg-[#59616B] transition-transform duration-300 ease-in-out ${isOpen ? "rotate-180" : ""} `}
            style={{ clipPath: "polygon(50% 100%, 0% 0%, 100% 0%)" }}
          ></div>
        </div>
      </div>

      <div
        className={`absolute bottom-full left-0 z-[1000] mb-1 max-h-28 w-269 overflow-y-auto rounded-md border border-[#D5DFF7] bg-[#23282E] p-0.5 shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] ${isOpen ? "block animate-fadeInDropdown" : "hidden"} `}
      >
        {dropdownItems.map((item, index) => (
          <div
            key={index}
            className="mx-0.5 my-0.5 flex min-h-10 w-[calc(100%-4px)] cursor-pointer items-center rounded bg-[#23282E] px-2 py-[6px] transition-colors duration-200 ease-in-out hover:bg-[#2A3441]"
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
