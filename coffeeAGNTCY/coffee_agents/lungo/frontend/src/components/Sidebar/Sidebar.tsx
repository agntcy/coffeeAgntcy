/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react"
import ErrorOutline from "@mui/icons-material/ErrorOutline"
import {
  Box,
  Drawer,
  List,
  Spinner,
  Stack,
  Typography,
} from "@open-ui-kit/core"
import { styled } from "@mui/material/styles"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import CatalogTree from "./CatalogTree"
import {
  buildCatalogSidebarLayout,
  buildInitialExpanded,
} from "./sidebar.utils"

const SIDEBAR_DRAWER_WIDTH = "16.5rem"

const StyledDrawer = styled(Drawer)(({ theme }) => ({
  width: SIDEBAR_DRAWER_WIDTH,
  flexShrink: 0,
  whiteSpace: "nowrap",
  boxSizing: "border-box",
  "& .MuiDrawer-paper": {
    width: SIDEBAR_DRAWER_WIDTH,
    overflowX: "hidden",
    backgroundColor: theme.palette.background.paper,
    borderRadius: 0,
  },
}))

interface SidebarProps {
  selectedWorkflowSummary: WorkflowSummary | null
  summaries: WorkflowSummary[] | null
  isLoading: boolean
  error: string | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedWorkflowSummary,
  summaries,
  isLoading,
  error,
  onSelectWorkflow,
}) => {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())

  const layout = useMemo(
    () => buildCatalogSidebarLayout(summaries ?? []),
    [summaries],
  )

  const toggleExpandableDropdown = useCallback((key: string) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }, [])

  const catalogSummariesRef = useRef<WorkflowSummary[] | null>(null)

  useEffect(() => {
    if (summaries === null) return
    if (catalogSummariesRef.current === summaries) return
    catalogSummariesRef.current = summaries
    setExpandedKeys(buildInitialExpanded(layout.implementedPatterns))
  }, [layout.implementedPatterns, summaries])

  return (
    <StyledDrawer
      variant="permanent"
      data-testid="sidebar"
      open
      slotProps={{
        paper: {
          sx: {
            position: "relative",
            display: "flex",
            flexDirection: "column",
            height: "100%",
            p: 3,
            pr: 0,
          },
        },
      }}
    >
      <List
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 3,
          alignItems: "baseline",
          overflowY: "auto",
          p: 0,
          pr: 3,
          width: "100%",
          minHeight: 0,
          flex: 1,
        }}
      >
        <Box
          component="nav"
          aria-label="Agentic patterns catalog"
          sx={{
            width: "100%",
            minWidth: 0,
            alignSelf: "stretch",
            flex: 1,
            minHeight: 0,
            overflow: "auto",
          }}
        >
          <Stack direction="column" sx={{ width: "100%" }}>
            {isLoading ? (
              <Stack
                direction="row"
                alignItems="center"
                spacing={1.5}
                role="status"
                aria-label="Loading workflows"
                sx={{ px: 2.5, py: 1 }}
              >
                <Spinner size={16} thickness={4} />
                <Typography variant="body2" sx={{ opacity: 0.6 }}>
                  Loading workflows...
                </Typography>
              </Stack>
            ) : null}

            {!isLoading && error !== null ? (
              <Stack
                direction="row"
                alignItems="center"
                spacing={1}
                role="alert"
                sx={{ px: 2.5, py: 1, opacity: 0.8 }}
              >
                <ErrorOutline sx={{ fontSize: 16 }} />
                <Typography variant="caption">Menu is unavailable</Typography>
              </Stack>
            ) : null}

            {!isLoading && error === null ? (
              <CatalogTree
                layout={layout}
                expandedKeys={expandedKeys}
                toggleExpandableDropdown={toggleExpandableDropdown}
                selectedWorkflowSummary={selectedWorkflowSummary}
                onSelectWorkflow={onSelectWorkflow}
              />
            ) : null}
          </Stack>
        </Box>
      </List>
    </StyledDrawer>
  )
}

export default Sidebar
