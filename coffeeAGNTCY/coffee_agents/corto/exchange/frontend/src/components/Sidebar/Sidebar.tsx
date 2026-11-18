/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box, List, Typography } from "@open-ui-kit/core"
import { getAppShellBackgroundColor } from "@/components/MainArea/mainAreaBackground"
import SidebarItem from "./sidebarItem"

export interface SidebarProps {
  embeddedInDrawer?: boolean
  showHeading?: boolean
}

const Sidebar: React.FC<SidebarProps> = ({
  embeddedInDrawer = false,
  showHeading = true,
}) => {
  return (
    <Box
      component="aside"
      aria-label="Conversation catalog"
      sx={(theme) => ({
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
        width: "100%",
        height: embeddedInDrawer ? "auto" : "100%",
        minWidth: 0,
        minHeight: 0,
        overflow: "hidden",
        backgroundColor: embeddedInDrawer
          ? "transparent"
          : getAppShellBackgroundColor(theme),
        p: embeddedInDrawer ? 0 : 3,
      })}
    >
      {showHeading ? (
        <Typography variant="h6" sx={{ flexShrink: 0, mb: 2 }}>
          Conversation: Coffee Grading
        </Typography>
      ) : null}
      <List component="nav" aria-label="Agent patterns" disablePadding>
        <SidebarItem title="Agent to Agent" isSelected onClick={() => {}} />
      </List>
    </Box>
  )
}

export default Sidebar
