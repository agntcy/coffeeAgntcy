/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { IconButton } from "@open-ui-kit/core"
import ExpandLess from "@mui/icons-material/ExpandLess"
import { cn } from "@/utils/cn"

interface SidebarDropdownProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
  isNested?: boolean
  titleClassName?: string
}

const SidebarDropdown: React.FC<SidebarDropdownProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
  titleClassName,
}) => {
  return (
    <div className="flex w-full flex-col items-start p-0">
      <div
        className={cn(
          "flex w-full items-start gap-2 bg-sidebar-background py-2 pl-8 pr-5 transition-colors hover:bg-sidebar-item-selected",
          titleClassName,
        )}
      >
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
        >
          {title}
        </span>
        <IconButton
          size="small"
          color="inherit"
          aria-expanded={isExpanded}
          aria-label={`${isExpanded ? "Collapse" : "Expand"} ${title}`}
          onClick={onToggle}
          sx={{
            flex: "none",
            mt: "-2px",
            p: 0.25,
          }}
        >
          <ExpandLess
            sx={{
              fontSize: 20,
              transition: "transform 150ms ease",
              transform: isExpanded ? "rotate(0deg)" : "rotate(180deg)",
            }}
          />
        </IconButton>
      </div>

      {isExpanded && <div className="flex w-full flex-col">{children}</div>}
    </div>
  )
}

export default SidebarDropdown
