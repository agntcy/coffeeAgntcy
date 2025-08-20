/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useRef, useEffect } from "react"

interface CoffeePromptsDropdownProps {
  visible: boolean
  onSelect: (query: string) => void
}

const CoffeePromptsDropdown: React.FC<CoffeePromptsDropdownProps> = ({
  visible,
  onSelect,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const buyerPrompts = [
    "What yield do the farms have?",
    "What is the current inventory?",
    "I'd like to buy 200 lbs quantity of coffee and who can fulfil it?",
    "List all the coffee farms",
    "Where can I get the best coffee with flavors like Ethiopian?",
  ]

  const purchaserPrompts = [
    "I'd like to buy 200 lbs quantity of coffee at USD 500 price from Colombia",
    "What is the status of my purchase?",
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
    <div className="flex items-center gap-3">
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
          className={`absolute bottom-full left-0 z-[1000] mb-1 h-[365px] w-269 overflow-y-auto rounded-[6px] border border-[#D5DFF7] bg-[#23282E] px-[2px] py-0 opacity-100 shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] ${isOpen ? "block animate-fadeInDropdown" : "hidden"} `}
        >
          <div className="px-2 py-2">
            <div
              className="mb-2 px-2 font-inter text-sm font-normal leading-5 tracking-[0%] text-[#889099]"
              style={{
                width: "245px",
                height: "20px",
                opacity: 1,
              }}
            >
              BUYER
            </div>
            {buyerPrompts.map((item, index) => (
              <div
                key={`buyer-${index}`}
                className="mx-0.5 my-0.5 flex min-h-10 w-[calc(100%-4px)] cursor-pointer items-center rounded bg-[#23282E] px-2 py-[6px] transition-colors duration-200 ease-in-out hover:bg-[#2A3441]"
                onClick={() => handleItemClick(item)}
              >
                <div className="w-full break-words font-cisco text-sm font-normal leading-5 tracking-[0%] text-white">
                  {item}
                </div>
              </div>
            ))}
          </div>

          <div className="mx-2 my-2 border-t border-[#889099]"></div>

          <div className="px-2 py-2">
            <div className="mb-2 h-[36px] w-[265px] gap-2 bg-[#23282E] pb-2 pl-[10px] pr-[10px] pt-2 font-inter text-sm font-normal leading-5 tracking-[0%] text-[#889099] opacity-100">
              PURCHASER
            </div>
            {purchaserPrompts.map((item, index) => (
              <div
                key={`purchaser-${index}`}
                className="mx-0.5 my-0.5 flex min-h-10 w-[calc(100%-4px)] cursor-pointer items-center rounded bg-[#23282E] px-2 py-[6px] transition-colors duration-200 ease-in-out hover:bg-[#2A3441]"
                onClick={() => handleItemClick(item)}
              >
                <div className="w-full break-words font-cisco text-sm font-normal leading-5 tracking-[0%] text-white">
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

export default CoffeePromptsDropdown
