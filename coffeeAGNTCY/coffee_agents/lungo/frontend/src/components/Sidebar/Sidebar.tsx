/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useEffect, useMemo, useState } from "react"
import { Spinner } from "@open-ui-kit/core"
import ErrorOutline from "@mui/icons-material/ErrorOutline"
import { PatternType } from "@/utils/patternUtils"
import {
  fetchWorkflowSummaries,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import {
  groupWorkflowsByPatternAndUseCase,
  type CatalogSidebarEntry,
} from "@/utils/sidebarHierarchy"
import { logger } from "@/utils/logger"
import CatalogTree from "./CatalogTree"
import SidebarItem from "./sidebarItem"
import { makePatternKey, makeScenarioKey } from "./sidebarKeys"

interface SidebarProps {
  selectedPattern: PatternType
  selectedPlaceholderPatternName: string | null
  onPatternChange: (pattern: PatternType) => void
  onPlaceholderPatternSelect: (catalogPatternName: string) => void
}

const CATALOG_ENDPOINT = "/agentic-workflows/"
/**
 * Total number of attempts (one initial request + this many retries) before
 * the catalog menu fetch is treated as failed. Mirrors common UX patterns
 * where transient hiccups don't immediately surface an error to the user.
 */
const CATALOG_FETCH_MAX_RETRIES = 2
/** Backoff (ms) between consecutive retry attempts. */
const CATALOG_FETCH_RETRY_DELAY_MS = 750

/**
 * Initial expansion set: every pattern and every use-case+scenario row open,
 * mirroring the previous static sidebar UX where every dropdown was open by
 * default.
 */
const buildInitialExpanded = (tree: CatalogSidebarEntry[]): Set<string> => {
  const next = new Set<string>()
  for (const entry of tree) {
    if (entry.kind !== "pattern" || entry.variant !== "implemented") {
      continue
    }
    const pattern = entry.node
    next.add(makePatternKey(pattern.name))
    for (const ucs of pattern.useCaseScenarios) {
      next.add(makeScenarioKey(pattern.name, ucs.useCase, ucs.scenario))
    }
  }
  return next
}

const sleep = (ms: number, signal: AbortSignal): Promise<void> =>
  new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException("Aborted", "AbortError"))
      return
    }
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      clearTimeout(timer)
      reject(new DOMException("Aborted", "AbortError"))
    }
    signal.addEventListener("abort", onAbort, { once: true })
  })

/**
 * Fetch the workflow catalog with a small retry budget so transient network
 * blips don't immediately surface as an error to the user. Each retry uses
 * the same `AbortSignal`, so unmount/cleanup short-circuits the loop.
 */
const fetchWorkflowSummariesWithRetry = async (
  signal: AbortSignal,
): Promise<WorkflowSummary[]> => {
  let lastError: unknown
  for (let attempt = 0; attempt <= CATALOG_FETCH_MAX_RETRIES; attempt += 1) {
    try {
      return await fetchWorkflowSummaries(signal)
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") throw err
      lastError = err
      if (attempt < CATALOG_FETCH_MAX_RETRIES) {
        await sleep(CATALOG_FETCH_RETRY_DELAY_MS, signal)
      }
    }
  }
  throw lastError
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedPattern,
  selectedPlaceholderPatternName,
  onPatternChange,
  onPlaceholderPatternSelect,
}) => {
  const [summaries, setSummaries] = useState<WorkflowSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  useEffect(() => {
    const controller = new AbortController()
    setError(null)
    fetchWorkflowSummariesWithRetry(controller.signal)
      .then((rows) => {
        setSummaries(rows)
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        logger.apiError(CATALOG_ENDPOINT, err)
        setError(err instanceof Error ? err.message : String(err))
      })
    return () => controller.abort()
  }, [])

  const tree = useMemo(
    () => groupWorkflowsByPatternAndUseCase(summaries ?? []),
    [summaries],
  )

  useEffect(() => {
    if (summaries === null) return
    setExpanded(buildInitialExpanded(tree))
  }, [tree, summaries])

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
        <div className="flex flex-none min-h-[36px] w-full items-center gap-2 rounded py-2 pl-2 pr-5">
          <span className="flex-1 font-inter text-base font-semibold leading-6 tracking-[0.15px] text-sidebar-text">
            Agentic Patterns
          </span>
        </div>

        {summaries === null && error === null && (
          <div
            className="flex flex-none w-full items-center gap-3 px-5 py-2"
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
            className="flex flex-none w-full items-center gap-2 px-5 py-2 text-xs leading-4 text-sidebar-text opacity-80"
            role="alert"
          >
            <ErrorOutline sx={{ fontSize: 16 }} />
            <span>Menu is unavailable</span>
          </div>
        )}

        {summaries !== null && error === null && (
          <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden pr-1">
            <CatalogTree
              tree={tree}
              expanded={expanded}
              onToggle={toggle}
              selectedPattern={selectedPattern}
              selectedPlaceholderPatternName={selectedPlaceholderPatternName}
              onPatternChange={onPatternChange}
              onPlaceholderPatternSelect={onPlaceholderPatternSelect}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar
