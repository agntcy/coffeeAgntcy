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
}) => {
  return (
    <div className="flex w-[288px] flex-col items-start p-0">
      <div
        className="bg-primary-bg flex h-9 w-[288px] cursor-pointer items-start gap-2 px-5 py-2 pl-8 transition-colors hover:bg-[#373C42]"
        onClick={onToggle}
      >
        <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-white">
          {title}
        </span>
        <ChevronUp
          className={`h-5 w-5 flex-none text-[#E8E9EA] transition-transform ${
            isExpanded ? "rotate-0" : "rotate-180"
          }`}
        />
      </div>

      {isExpanded && <div className="flex w-[288px] flex-col">{children}</div>}
    </div>
  )
}

export default SidebarDropdown
