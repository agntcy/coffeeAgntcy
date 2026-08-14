/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Box, Message, Spinner, Stack, Typography } from "@open-ui-kit/core"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { getAppShellBackgroundColor } from "../MainArea/mainAreaBackground"
import { transparentScrollbarSx } from "@/utils/transparentScrollbarSx"
import CatalogTree from "./CatalogTree"
import {
  buildCatalogSidebarLayout,
  buildInitialExpanded,
  patternCategoryOrderFromApi,
} from "./sidebar.utils"

interface SidebarProps {
  selectedWorkflowSummary: WorkflowSummary | null
  summaries: WorkflowSummary[] | null
  patternCategories: readonly { name: string }[] | null
  patternCategoriesError: string | null
  isLoading: boolean
  error: string | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
  selectedReferencePattern?: string | null
  onSelectReferencePattern?: (patternName: string) => void
  selectedPatternCategory?: string | null
  onSelectPatternCategory?: (categoryName: string) => void
  /** When true, omit outer panel padding (e.g. inside OUK SideDrawer). */
  embeddedInDrawer?: boolean
  /** When false, hide the "Agentic Patterns" heading (drawer supplies its own title). */
  showHeading?: boolean
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedWorkflowSummary,
  summaries,
  patternCategories,
  patternCategoriesError,
  isLoading,
  error,
  onSelectWorkflow,
  selectedReferencePattern,
  onSelectReferencePattern,
  selectedPatternCategory,
  onSelectPatternCategory,
  embeddedInDrawer = false,
  showHeading = true,
}) => {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())

  const categoryOrder = useMemo(
    () => patternCategoryOrderFromApi(patternCategories ?? []),
    [patternCategories],
  )

  const layout = useMemo(
    () => buildCatalogSidebarLayout(summaries ?? [], categoryOrder),
    [summaries, categoryOrder],
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
    setExpandedKeys(buildInitialExpanded(layout))
  }, [layout, summaries])

  return (
    <Box
      component="aside"
      aria-label="Workflow catalog"
      data-testid="sidebar"
      sx={{
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
        width: "100%",
        height: embeddedInDrawer ? "auto" : "100%",
        minWidth: 0,
        minHeight: 0,
        overflow: "hidden",
        backgroundColor: (theme) =>
          embeddedInDrawer ? "transparent" : getAppShellBackgroundColor(theme),
        p: embeddedInDrawer ? 0 : 3,
        pr: embeddedInDrawer ? 0 : 0,
      }}
    >
      {showHeading ? (
        <Typography variant="h6" sx={{ flexShrink: 0, mb: 2 }}>
          Agentic Patterns
        </Typography>
      ) : null}
      <Box
        component="nav"
        aria-label="Agentic patterns catalog"
        sx={(theme) => ({
          width: "100%",
          minWidth: 0,
          flex: embeddedInDrawer ? "0 1 auto" : 1,
          minHeight: 0,
          overflowY: embeddedInDrawer ? "visible" : "auto",
          overflowX: "hidden",
          pr: embeddedInDrawer ? 0 : 3,
          ...transparentScrollbarSx(theme),
        })}
      >
        <Stack direction="column" sx={{ width: "100%", gap: 3 }}>
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

          {!isLoading
            ? [error, error === null ? patternCategoriesError : null]
                .filter((message): message is string => message !== null)
                .map((message) => (
                  <Message
                    key={message}
                    type="error"
                    hideClose
                    role="alert"
                    sx={{ my: 1, width: "100%", textWrap: "wrap" }}
                  >
                    {message}
                  </Message>
                ))
            : null}

          {!isLoading && error === null ? (
            <CatalogTree
              layout={layout}
              expandedKeys={expandedKeys}
              toggleExpandableDropdown={toggleExpandableDropdown}
              selectedWorkflowSummary={selectedWorkflowSummary}
              onSelectWorkflow={onSelectWorkflow}
              selectedReferencePattern={selectedReferencePattern}
              onSelectReferencePattern={onSelectReferencePattern}
              selectedPatternCategory={selectedPatternCategory}
              onSelectPatternCategory={onSelectPatternCategory}
              separateReferenceCategoryNavigation={embeddedInDrawer}
            />
          ) : null}
        </Stack>
      </Box>
    </Box>
  )
}

export type { SidebarProps }
export default Sidebar
