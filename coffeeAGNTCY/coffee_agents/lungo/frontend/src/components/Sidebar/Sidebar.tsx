/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react"
import ErrorOutline from "@mui/icons-material/ErrorOutline"
import { Box, Spinner, Stack, Typography } from "@open-ui-kit/core"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import CatalogTree from "./CatalogTree"
import { SidebarFrame } from "./SidebarFrame"
import {
  buildCatalogSidebarLayout,
  buildInitialExpanded,
  type CatalogSidebarLayout,
} from "./sidebar.utils"

interface SidebarProps {
  selectedWorkflowSummary: WorkflowSummary | null
  summaries: WorkflowSummary[] | null
  isLoading: boolean
  error: string | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
}

interface SidebarCatalogNavigationSlotProps {
  iconOnly?: boolean
  layout: CatalogSidebarLayout
  expandedKeys: Set<string>
  toggleExpandableDropdown: (key: string) => void
  selectedWorkflowSummary: WorkflowSummary | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
  isLoading: boolean
  error: string | null
}

/**
 * When false, the rail stays expanded, the collapse toggle is not rendered, and width
 * does not animate to the narrow rail.
 */
const SIDEBAR_FRAME_COLLAPSIBLE = false

function SidebarCatalogNavigationSlot({
  iconOnly = false,
  layout,
  expandedKeys,
  toggleExpandableDropdown,
  selectedWorkflowSummary,
  onSelectWorkflow,
  isLoading,
  error,
}: SidebarCatalogNavigationSlotProps) {
  if (iconOnly) {
    return null
  }

  return (
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
  )
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
    <SidebarFrame
      collapsible={SIDEBAR_FRAME_COLLAPSIBLE}
      initialOpen
      navigationItems={[
        <SidebarCatalogNavigationSlot
          key="catalog-nav"
          layout={layout}
          expandedKeys={expandedKeys}
          toggleExpandableDropdown={toggleExpandableDropdown}
          selectedWorkflowSummary={selectedWorkflowSummary}
          onSelectWorkflow={onSelectWorkflow}
          isLoading={isLoading}
          error={error}
        />,
      ]}
    />
  )
}

export default Sidebar
