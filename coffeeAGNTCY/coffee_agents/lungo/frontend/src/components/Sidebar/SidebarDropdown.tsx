/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box, ListItemButton, Stack, Typography } from "@open-ui-kit/core"
import ExpandLess from "@mui/icons-material/ExpandLess"
import { sidebarBorderRadius, sidebarItemMt } from "./sidebarSx"

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
  const toggleId = React.useId()
  const titleId = React.useId()
  const panelId = React.useId()
  const toggleLabel = `${isExpanded ? "Collapse" : "Expand"} ${title}`

  return (
    <Stack direction="column" alignItems="flex-start">
      <ListItemButton
        component="button"
        type="button"
        id={toggleId}
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={panelId}
        aria-label={toggleLabel}
        sx={{
          width: "100%",
          justifyContent: "space-between",
          borderRadius: sidebarBorderRadius,
          textWrap: "auto",
          mt: sidebarItemMt,
        }}
      >
        <Typography id={titleId} component="span" variant="body1">
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

      <Stack
        id={panelId}
        role="region"
        aria-labelledby={titleId}
        hidden={!isExpanded}
        direction="column"
        sx={{ width: "100%", pl: 2 }}
      >
        {children}
      </Stack>
    </Stack>
  )
}

export default SidebarDropdown
