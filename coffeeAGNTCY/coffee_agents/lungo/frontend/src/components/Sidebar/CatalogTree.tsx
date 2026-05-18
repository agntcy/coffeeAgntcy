/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback } from "react"
import {
  mapWorkflowNameToSlug,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import {
  A2A_SLIM_MENU_LABEL,
  isPlaceholderWorkflow,
  type CatalogSidebarLayout,
  type UseCaseScenarioNode,
  type WorkflowNode,
} from "@/utils/sidebarHierarchy"
import { openWorkflowDocumentationInNewTab } from "@/utils/workflowDocumentationGithub"
import { cn } from "@/utils/cn"
import SidebarItem from "./sidebarItem"
import SidebarDropdown from "./SidebarDropdown"
import UseCaseDropdown from "./UseCaseDropdown"
import WorkflowDropdown from "./WorkflowDropdown"
import {
  makePatternKey,
  makeScenarioKey,
  makeWorkflowKey,
  REFERENCE_LIBRARY_KEY,
} from "./sidebarKeys"

interface CatalogTreeProps {
  layout: CatalogSidebarLayout
  expanded: Set<string>
  onToggle: (key: string) => void
  selectedWorkflowSummary: WorkflowSummary | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
}

const CatalogTree: React.FC<CatalogTreeProps> = ({
  layout,
  expanded,
  onToggle,
  selectedWorkflowSummary,
  onSelectWorkflow,
}) => {
  const { implementedPatterns, referencePatternNames } = layout

  const openDoc = useCallback((catalogName: string) => {
    openWorkflowDocumentationInNewTab(catalogName)
  }, [])

  const renderWorkflow = (
    patternName: string,
    ucs: UseCaseScenarioNode,
    workflow: WorkflowNode,
  ): React.ReactNode => {
    const { summary, display } = workflow
    const isUnmapped = mapWorkflowNameToSlug(summary.name) === null
    const isSelected = selectedWorkflowSummary?.name === summary.name
    const showWorkflowDoc = !isPlaceholderWorkflow(summary)

    if (display === "slim_transport") {
      const workflowKey = makeWorkflowKey(
        patternName,
        ucs.useCase,
        ucs.scenario,
        summary.name,
      )
      return (
        <WorkflowDropdown
          key={summary.name}
          title={summary.name}
          isExpanded={expanded.has(workflowKey)}
          onToggle={() => onToggle(workflowKey)}
          isChildSelected={isSelected}
        >
          <SidebarItem
            title={A2A_SLIM_MENU_LABEL}
            isSelected={isSelected}
            onClick={isUnmapped ? undefined : () => onSelectWorkflow(summary)}
            documentationCatalogName={
              showWorkflowDoc ? summary.name : undefined
            }
            onOpenDocumentation={showWorkflowDoc ? openDoc : undefined}
            className={cn(
              "pl-14",
              isUnmapped && "pointer-events-none cursor-not-allowed opacity-50",
            )}
          />
        </WorkflowDropdown>
      )
    }

    return (
      <SidebarItem
        key={summary.name}
        title={summary.name}
        isSelected={isSelected}
        onClick={isUnmapped ? undefined : () => onSelectWorkflow(summary)}
        documentationCatalogName={showWorkflowDoc ? summary.name : undefined}
        onOpenDocumentation={showWorkflowDoc ? openDoc : undefined}
        className={cn(
          "pl-10",
          isUnmapped && "pointer-events-none cursor-not-allowed opacity-50",
        )}
      />
    )
  }

  if (implementedPatterns.length === 0 && referencePatternNames.length === 0) {
    return <SidebarItem title="No workflows available" className="opacity-60" />
  }

  const showSeparator =
    implementedPatterns.length > 0 && referencePatternNames.length > 0

  return (
    <>
      {implementedPatterns.map((pattern) => {
        const pKey = makePatternKey(pattern.name)
        return (
          <SidebarDropdown
            key={pKey}
            title={pattern.name}
            isExpanded={expanded.has(pKey)}
            onToggle={() => onToggle(pKey)}
            titleClassName="pl-2"
          >
            {pattern.useCaseScenarios.map((ucs) => {
              const ucsKey = makeScenarioKey(
                pattern.name,
                ucs.useCase,
                ucs.scenario,
              )
              return (
                <UseCaseDropdown
                  key={ucsKey}
                  title={ucs.label}
                  isExpanded={expanded.has(ucsKey)}
                  onToggle={() => onToggle(ucsKey)}
                >
                  {ucs.workflows.map((workflow) =>
                    renderWorkflow(pattern.name, ucs, workflow),
                  )}
                </UseCaseDropdown>
              )
            })}
          </SidebarDropdown>
        )
      })}

      {showSeparator && (
        <div
          className="my-2 border-t border-sidebar-border px-2"
          role="separator"
          aria-hidden="true"
        />
      )}

      {referencePatternNames.length > 0 && (
        <SidebarDropdown
          title="Reference Library"
          isExpanded={expanded.has(REFERENCE_LIBRARY_KEY)}
          onToggle={() => onToggle(REFERENCE_LIBRARY_KEY)}
          titleClassName="pl-2"
        >
          {referencePatternNames.map((patternName) => (
            <button
              key={patternName}
              type="button"
              className="flex w-full items-start gap-2 bg-sidebar-background py-2 pl-8 pr-5 text-left font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text transition-colors hover:bg-sidebar-item-selected"
              onClick={() => openDoc(patternName)}
            >
              <span className="flex-1">{patternName}</span>
            </button>
          ))}
        </SidebarDropdown>
      )}
    </>
  )
}

export default CatalogTree
