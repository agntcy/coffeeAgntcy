/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import {
  IconButton,
  ListItemButton,
  Stack,
  Typography,
} from "@open-ui-kit/core"
import ExpandLess from "@mui/icons-material/ExpandLess"

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
    <Stack direction="column" alignItems="flex-start">
      <ListItemButton
        onClick={onToggle}
        aria-expanded={isExpanded}
        sx={{
          width: "100%",
          justifyContent: "space-between",
          backgroundColor: "transparent",
          borderRadius: "8px",
          textWrap: "auto",
          "& svg": {
            transition: "transform 0.2s ease",
            transform: isExpanded ? "rotate(0deg)" : "rotate(180deg)",
          },
        }}
      >
        <Typography component="span" variant="body1">
          {title}
        </Typography>
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
      </ListItemButton>

      {isExpanded ? (
        <Stack direction="column" sx={{ width: "100%", paddingLeft: "16px" }}>
          {children}
        </Stack>
      ) : null}
    </Stack>
  )
}

export default SidebarDropdown
