/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DescriptionOutlined from "@mui/icons-material/DescriptionOutlined"
import { cn } from "@/utils/cn"

interface SidebarItemProps {
  title: string
  isSelected?: boolean
  onClick?: () => void
  className?: string
  documentationCatalogName?: string
  onOpenDocumentation?: (catalogName: string) => void
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  title,
  isSelected = false,
  onClick,
  className,
  documentationCatalogName,
  onOpenDocumentation,
}) => {
  const showDoc =
    documentationCatalogName !== undefined && onOpenDocumentation !== undefined

  return (
    <div
      className={cn(
        "group relative flex w-full items-start gap-1 py-2 pl-12 pr-5 font-inter text-sm font-normal leading-5 text-sidebar-text transition-colors hover:bg-sidebar-item-selected",
        isSelected ? "bg-sidebar-item-selected" : "bg-sidebar-background",
        onClick ? "cursor-pointer" : "cursor-default",
        className,
      )}
      onClick={onClick}
    >
      <span className="min-w-0 flex-1 pr-8">{title}</span>
      {showDoc && (
        <button
          type="button"
          className={cn(
            "absolute right-3 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md text-sidebar-text opacity-0 transition-opacity hover:bg-sidebar-item-selected group-hover:opacity-100",
            isSelected && "opacity-100",
          )}
          aria-label={`Open documentation for ${title}`}
          title="View documentation on GitHub"
          onClick={(e) => {
            e.stopPropagation()
            onOpenDocumentation(documentationCatalogName)
          }}
        >
          <DescriptionOutlined sx={{ fontSize: 16 }} />
        </button>
      )}
    </div>
  )
}

export default SidebarItem