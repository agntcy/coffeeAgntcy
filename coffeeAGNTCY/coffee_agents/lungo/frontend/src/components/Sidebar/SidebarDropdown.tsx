/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ListItemButton, Stack, Typography } from "@open-ui-kit/core"
import ExpandLess from "@mui/icons-material/ExpandLess"
import Box from "@mui/material/Box"

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
        aria-label={`${isExpanded ? "Collapse" : "Expand"} ${title}`}
        sx={{
          width: "100%",
          justifyContent: "space-between",
          backgroundColor: "transparent",
          borderRadius: "8px",
          textWrap: "auto",
        }}
      >
        <Typography component="span" variant="body1">
          {title}
        </Typography>
        <Box
          component="span"
          aria-hidden
          sx={{
            flex: "none",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            mt: "-2px",
            p: 0.25,
          }}
        >
          <ExpandLess
            sx={{
              transition: "transform 150ms ease",
              transform: isExpanded ? "rotate(0deg)" : "rotate(180deg)",
            }}
          />
        </Box>
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
