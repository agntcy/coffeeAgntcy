/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useMemo, useState } from "react"
import { PATTERNS, PatternType } from "@/utils/patternUtils"
import {
  fetchWorkflowSummaries,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import {
  groupWorkflowsByPatternAndUseCase,
  type PatternNode,
} from "@/utils/sidebarHierarchy"
import { logger } from "@/utils/logger"
import SidebarItem from "./sidebarItem"
import SidebarDropdown from "./SidebarDropdown"

interface SidebarProps {
  selectedPattern: PatternType
  onPatternChange: (pattern: PatternType) => void
}

const CATALOG_ENDPOINT = "/agentic-workflows/"

const makePatternKey = (patternName: string) => `pattern:${patternName}`
const makeUseCaseKey = (patternName: string, useCaseName: string) =>
  `pattern:${patternName}|usecase:${useCaseName}`

/**
 * Initial expansion set: every pattern and every use-case open, mirroring the
 * previous static sidebar UX where every dropdown was open by default.
 */
const buildInitialExpanded = (tree: PatternNode[]): Set<string> => {
  const next = new Set<string>()
  for (const pattern of tree) {
    next.add(makePatternKey(pattern.name))
    for (const useCase of pattern.useCases) {
      next.add(makeUseCaseKey(pattern.name, useCase.name))
    }
  }
  return next
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedPattern,
  onPatternChange,
}) => {
  const [summaries, setSummaries] = useState<WorkflowSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  useEffect(() => {
    const controller = new AbortController()
    fetchWorkflowSummaries(controller.signal)
      .then((rows) => {
        setSummaries(rows)
        setError(null)
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

  const toggle = (key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  return (
    <div className="flex h-full w-64 flex-none flex-col gap-5 border-r border-sidebar-border bg-sidebar-background font-inter lg:w-[320px]">
      <div className="flex h-full flex-1 flex-col gap-2 p-4">
        <div className="flex min-h-[36px] w-full items-center gap-2 rounded py-2 pl-2 pr-5">
          <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text">
            Agentic Patterns
          </span>
        </div>

        {summaries === null && error === null && (
          <SidebarItem title="Loading workflows..." className="opacity-60" />
        )}

        {error !== null && (
          <>
            <div className="px-5 py-1 text-xs leading-4 text-sidebar-text opacity-70">
              Couldn&apos;t load workflows from the catalog API. Showing the
              built-in menu.
            </div>
            <StaticFallbackTree
              selectedPattern={selectedPattern}
              onPatternChange={onPatternChange}
            />
          </>
        )}

        {summaries !== null && error === null && (
          <CatalogTree
            tree={tree}
            expanded={expanded}
            onToggle={toggle}
            selectedPattern={selectedPattern}
            onPatternChange={onPatternChange}
          />
        )}
      </div>
    </div>
  )
}

interface CatalogTreeProps {
  tree: PatternNode[]
  expanded: Set<string>
  onToggle: (key: string) => void
  selectedPattern: PatternType
  onPatternChange: (pattern: PatternType) => void
}

const CatalogTree: React.FC<CatalogTreeProps> = ({
  tree,
  expanded,
  onToggle,
  selectedPattern,
  onPatternChange,
}) => {
  if (tree.length === 0) {
    return <SidebarItem title="No workflows available" className="opacity-60" />
  }

  return (
    <>
      {tree.map((pattern) => {
        const pKey = makePatternKey(pattern.name)
        const renderUseCaseAsDropdown = pattern.useCases.length > 1
        return (
          <SidebarDropdown
            key={pKey}
            title={pattern.name}
            isExpanded={expanded.has(pKey)}
            onToggle={() => onToggle(pKey)}
          >
            {pattern.useCases.map((useCase) => {
              const ucKey = makeUseCaseKey(pattern.name, useCase.name)
              const items = useCase.workflows.map((workflow) => {
                const isUnknown = workflow.slug === null
                const isSelected =
                  !isUnknown && selectedPattern === workflow.slug
                return (
                  <SidebarItem
                    key={workflow.name}
                    title={workflow.name}
                    isSelected={isSelected}
                    onClick={
                      isUnknown
                        ? undefined
                        : () => onPatternChange(workflow.slug!)
                    }
                    className={
                      isUnknown
                        ? "pointer-events-none cursor-not-allowed opacity-50"
                        : renderUseCaseAsDropdown
                          ? "pl-16"
                          : ""
                    }
                  />
                )
              })

              if (!renderUseCaseAsDropdown) {
                return <React.Fragment key={ucKey}>{items}</React.Fragment>
              }
              return (
                <UseCaseDropdown
                  key={ucKey}
                  title={useCase.name}
                  isExpanded={expanded.has(ucKey)}
                  onToggle={() => onToggle(ucKey)}
                >
                  {items}
                </UseCaseDropdown>
              )
            })}
          </SidebarDropdown>
        )
      })}
    </>
  )
}

interface UseCaseDropdownProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

/**
 * Lightweight nested dropdown for the use-case level. Visually it matches
 * `SidebarDropdown` but indents one extra step so the pattern -> use-case
 * relationship reads clearly.
 */
const UseCaseDropdown: React.FC<UseCaseDropdownProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
}) => {
  return (
    <div className="flex w-full flex-col items-start p-0">
      <div className="flex w-full items-start gap-2 bg-sidebar-background py-2 pl-12 pr-5 transition-colors hover:bg-sidebar-item-selected">
        <span
          className="flex-1 cursor-pointer font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text"
          onClick={onToggle}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault()
              onToggle()
            }
          }}
          role="button"
          tabIndex={0}
          aria-expanded={isExpanded}
        >
          {title}
        </span>
      </div>
      {isExpanded && <div className="flex w-full flex-col">{children}</div>}
    </div>
  )
}

interface StaticFallbackTreeProps {
  selectedPattern: PatternType
  onPatternChange: (pattern: PatternType) => void
}

/**
 * Fallback tree rendered when the catalog API is unreachable. Mirrors the
 * pre-#540 static sidebar so the app stays usable even if the agentic
 * workflows service is down.
 */
const StaticFallbackTree: React.FC<StaticFallbackTreeProps> = ({
  selectedPattern,
  onPatternChange,
}) => {
  const [groupExpanded, setGroupExpanded] = useState(true)
  const [pubSubExpanded, setPubSubExpanded] = useState(true)
  const [pubSubStreamExpanded, setPubSubStreamExpanded] = useState(true)
  const [discoveryExpanded, setDiscoveryExpanded] = useState(true)

  return (
    <>
      <SidebarDropdown
        title="Secure Group Communication"
        isExpanded={groupExpanded}
        onToggle={() => setGroupExpanded((v) => !v)}
      >
        <SidebarItem
          title="A2A SLIM"
          isSelected={selectedPattern === PATTERNS.GROUP_COMMUNICATION}
          onClick={() => onPatternChange(PATTERNS.GROUP_COMMUNICATION)}
        />
      </SidebarDropdown>
      <SidebarDropdown
        title="Publish Subscribe"
        isExpanded={pubSubExpanded}
        onToggle={() => setPubSubExpanded((v) => !v)}
      >
        <SidebarItem
          title="A2A"
          isSelected={selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE}
          onClick={() => onPatternChange(PATTERNS.PUBLISH_SUBSCRIBE)}
        />
      </SidebarDropdown>
      <SidebarDropdown
        title="Publish Subscribe: Streaming"
        isExpanded={pubSubStreamExpanded}
        onToggle={() => setPubSubStreamExpanded((v) => !v)}
      >
        <SidebarItem
          title="A2A"
          isSelected={selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING}
          onClick={() => onPatternChange(PATTERNS.PUBLISH_SUBSCRIBE_STREAMING)}
        />
      </SidebarDropdown>
      <SidebarDropdown
        title="Recruiter"
        isExpanded={discoveryExpanded}
        onToggle={() => setDiscoveryExpanded((v) => !v)}
      >
        <SidebarItem
          title="A2A HTTP"
          isSelected={selectedPattern === PATTERNS.ON_DEMAND_DISCOVERY}
          onClick={() => onPatternChange(PATTERNS.ON_DEMAND_DISCOVERY)}
        />
      </SidebarDropdown>
    </>
  )
}

export default Sidebar
