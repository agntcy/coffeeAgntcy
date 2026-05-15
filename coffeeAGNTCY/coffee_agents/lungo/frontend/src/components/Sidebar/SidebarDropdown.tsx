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
    <div className="flex w-full flex-col items-start p-0">
      <div
        className="flex h-9 w-full cursor-pointer items-start gap-2 bg-sidebar-background py-2 pl-8 pr-5 transition-colors hover:bg-sidebar-item-selected"
        onClick={onToggle}
      >
        <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text">
          {title}
        </span>
        <ChevronUp
          className={`h-5 w-5 flex-none text-sidebar-text transition-transform ${
            isExpanded ? "rotate-0" : "rotate-180"
          }`}
        />
      </div>

      {isExpanded && <div className="flex w-full flex-col">{children}</div>}
    </div>
  )
}

export default SidebarDropdown
