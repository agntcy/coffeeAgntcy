/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ChevronUp } from "lucide-react"

interface SidebarDropdownProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
  isNested?: boolean
}

const SidebarDropdown: React.FC<SidebarDropdownProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
  isNested = false,
}) => {
  return (
    <div
      className="flex flex-col items-start p-0"
      style={{ width: "288px", height: "144px" }}
    >
      <div
        className={`flex cursor-pointer items-center justify-between gap-2 py-2 pr-5 transition-colors hover:bg-[#373C42] ${isNested ? "pl-8" : "pl-5"}`}
        onClick={onToggle}
        style={{
          width: "288px",
          height: "36px",
        }}
      >
        <span
          className="font-inter text-sm font-normal leading-5 tracking-wide text-white opacity-100"
          style={{
            width: "208px",
            height: "20px",
          }}
        >
          {title}
        </span>
        <ChevronUp
          className={`order-2 h-5 w-5 flex-none grow-0 text-[#E8E9EA] opacity-100 transition-transform ${
            isExpanded ? "rotate-0" : "rotate-180"
          }`}
        />
      </div>

      {isExpanded && <div className="flex flex-col">{children}</div>}
    </div>
  )
}

export default SidebarDropdown
