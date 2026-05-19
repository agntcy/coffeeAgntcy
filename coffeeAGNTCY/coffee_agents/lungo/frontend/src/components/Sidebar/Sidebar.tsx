/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useEffect, useMemo, useState } from "react"
import { Spinner } from "@open-ui-kit/core"
import ErrorOutline from "@mui/icons-material/ErrorOutline"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import {
  buildCatalogSidebarLayout,
  type PatternNode,
} from "@/utils/sidebarHierarchy"
import CatalogTree from "./CatalogTree"
import SidebarItem from "./sidebarItem"
import { makePatternKey, makeScenarioKey, makeWorkflowKey } from "./sidebarKeys"

interface SidebarProps {
  selectedWorkflowSummary: WorkflowSummary | null
  summaries: WorkflowSummary[] | null
  error: string | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
}

const buildInitialExpanded = (
  implementedPatterns: PatternNode[],
): Set<string> => {
  const next = new Set<string>()
  for (const pattern of implementedPatterns) {
    next.add(makePatternKey(pattern.name))
    for (const ucs of pattern.useCaseScenarios) {
      next.add(makeScenarioKey(pattern.name, ucs.useCase, ucs.scenario))
      for (const workflow of ucs.workflows) {
        if (workflow.display === "slim_transport") {
          next.add(
            makeWorkflowKey(
              pattern.name,
              ucs.useCase,
              ucs.scenario,
              workflow.summary.name,
            ),
          )
        }
      }
    }
  }
  return next
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedWorkflowSummary,
  summaries,
  error,
  onSelectWorkflow,
}) => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const layout = useMemo(
    () => buildCatalogSidebarLayout(summaries ?? []),
    [summaries],
  )

  useEffect(() => {
    if (summaries === null) return
    setExpanded(buildInitialExpanded(layout.implementedPatterns))
  }, [layout.implementedPatterns, summaries])

  const toggle = useCallback((key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }, [])

  return (
    <div className="flex h-full min-h-0 w-64 flex-none flex-col border-r border-sidebar-border bg-sidebar-background font-inter lg:w-[320px]">
      <div className="flex min-h-0 flex-1 flex-col gap-2 p-4">
        <div className="flex min-h-[36px] w-full flex-none items-center gap-2 rounded py-2 pl-2 pr-5">
          <span className="flex-1 font-inter text-base font-semibold leading-6 tracking-[0.15px] text-sidebar-text">
            Agentic Patterns
          </span>
        </div>

        {summaries === null && error === null && (
          <div
            className="flex w-full flex-none items-center gap-3 px-5 py-2"
            role="status"
            aria-label="Loading workflows"
          >
            <Spinner size={16} thickness={4} />
            <SidebarItem
              title="Loading workflows..."
              className="flex-1 px-0 py-0 opacity-60 hover:bg-transparent"
            />
          </div>
        )}

        {error !== null && (
          <div
            className="flex w-full flex-none items-center gap-2 px-5 py-2 text-xs leading-4 text-sidebar-text opacity-80"
            role="alert"
          >
            <ErrorOutline sx={{ fontSize: 16 }} />
            <span>Menu is unavailable</span>
          </div>
        )}

        {summaries !== null && error === null && (
          <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden pr-1">
            <CatalogTree
              layout={layout}
              expanded={expanded}
              onToggle={toggle}
              selectedWorkflowSummary={selectedWorkflowSummary}
              onSelectWorkflow={onSelectWorkflow}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar
