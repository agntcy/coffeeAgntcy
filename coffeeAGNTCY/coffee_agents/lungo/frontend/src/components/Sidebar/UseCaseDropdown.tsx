/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"

interface UseCaseDropdownProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

/**
 * Lightweight nested dropdown for the use-case level. Visually it matches
 * `SidebarDropdown` but indents one step further so the pattern -> use-case
 * relationship reads clearly.
 */
const UseCaseDropdown: React.FC<UseCaseDropdownProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
}) => {
  return (
    <div className="flex w-full flex-col items-start p-0">
      <div className="flex w-full items-start gap-2 bg-sidebar-background py-2 pl-6 pr-5 transition-colors hover:bg-sidebar-item-selected">
        <span
          className="flex-1 cursor-pointer font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text"
          onClick={onToggle}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault()
              onToggle()
            }
          }}
          role="button"
          tabIndex={0}
          aria-expanded={isExpanded}
        >
          {title}
        </span>
      </div>
      {isExpanded && <div className="flex w-full flex-col">{children}</div>}
    </div>
  )
}

export default UseCaseDropdown
