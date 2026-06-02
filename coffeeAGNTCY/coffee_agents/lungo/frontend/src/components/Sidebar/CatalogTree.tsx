/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback } from "react"
import { Box, List, Typography } from "@open-ui-kit/core"
import {
  mapWorkflowNameToSlug,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import { openWorkflowDocumentationInNewTab } from "@/utils/workflowDocumentationGithub"
import SidebarDropdown from "./SidebarDropdown"
import SidebarItem from "./SidebarItem"
import {
  makePatternKey,
  makeScenarioKey,
  makeUseCaseKey,
  REFERENCE_LIBRARY_KEY,
  type CatalogSidebarLayout,
  type PatternNode,
  type UseCaseScenarioNode,
  type WorkflowNode,
} from "./sidebar.utils"

interface CatalogTreeProps {
  layout: CatalogSidebarLayout
  expandedKeys: Set<string>
  toggleExpandableDropdown: (key: string) => void
  selectedWorkflowSummary: WorkflowSummary | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
}

const groupScenariosByUseCase = (
  scenarios: readonly UseCaseScenarioNode[],
): Map<string, UseCaseScenarioNode[]> => {
  const byUseCase = new Map<string, UseCaseScenarioNode[]>()
  for (const ucs of scenarios) {
    const list = byUseCase.get(ucs.useCase)
    if (list === undefined) {
      byUseCase.set(ucs.useCase, [ucs])
    } else {
      list.push(ucs)
    }
  }
  return byUseCase
}

const CatalogTree: React.FC<CatalogTreeProps> = ({
  layout,
  expandedKeys,
  toggleExpandableDropdown,
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
    const { summary } = workflow
    const isUnmapped = mapWorkflowNameToSlug(summary.name) === null
    const isSelected = selectedWorkflowSummary?.name === summary.name

    return (
      <SidebarItem
        key={`${patternName}|${ucs.useCase}|${ucs.scenario}|${summary.name}`}
        title={summary.name}
        isSelected={isSelected}
        disabled={isUnmapped}
        documentationCatalogName={summary.name}
        onClick={isUnmapped ? undefined : () => onSelectWorkflow(summary)}
      />
    )
  }

  const renderPattern = (pattern: PatternNode): React.ReactNode => {
    const patternKey = makePatternKey(pattern.name)
    const byUseCase = groupScenariosByUseCase(pattern.useCaseScenarios)

    return (
      <SidebarDropdown
        key={patternKey}
        title={pattern.name}
        isExpanded={expandedKeys.has(patternKey)}
        onToggle={() => toggleExpandableDropdown(patternKey)}
      >
        {[...byUseCase.entries()].map(([useCase, scenarios]) => {
          const useCaseKey = makeUseCaseKey(pattern.name, useCase)
          return (
            <SidebarDropdown
              key={useCaseKey}
              title={useCase}
              isExpanded={expandedKeys.has(useCaseKey)}
              onToggle={() => toggleExpandableDropdown(useCaseKey)}
            >
              {scenarios.map((ucs) => {
                const scenarioKey = makeScenarioKey(
                  pattern.name,
                  ucs.useCase,
                  ucs.scenario,
                )
                return (
                  <SidebarDropdown
                    key={scenarioKey}
                    title={ucs.scenario}
                    isExpanded={expandedKeys.has(scenarioKey)}
                    onToggle={() => toggleExpandableDropdown(scenarioKey)}
                  >
                    {ucs.workflows.map((workflow) =>
                      renderWorkflow(pattern.name, ucs, workflow),
                    )}
                  </SidebarDropdown>
                )
              })}
            </SidebarDropdown>
          )
        })}
      </SidebarDropdown>
    )
  }

  if (implementedPatterns.length === 0 && referencePatternNames.length === 0) {
    return (
      <Typography variant="body2" sx={{ px: 2.5, py: 1, opacity: 0.6 }}>
        No workflows available
      </Typography>
    )
  }

  const showSeparator =
    implementedPatterns.length > 0 && referencePatternNames.length > 0

  return (
    <List component="div" disablePadding sx={{ width: "100%" }}>
      {implementedPatterns.map(renderPattern)}

      {showSeparator ? (
        <Box
          role="separator"
          aria-hidden
          sx={{
            width: "100%",
            my: 1,
            borderTop: 1,
            borderColor: "divider",
          }}
        />
      ) : null}

      {referencePatternNames.length > 0 ? (
        <SidebarDropdown
          title="Reference Library"
          isExpanded={expandedKeys.has(REFERENCE_LIBRARY_KEY)}
          onToggle={() => toggleExpandableDropdown(REFERENCE_LIBRARY_KEY)}
        >
          {referencePatternNames.map((patternName) => (
            <SidebarItem
              key={patternName}
              title={patternName}
              documentationCatalogName={patternName}
              onClick={() => openDoc(patternName)}
            />
          ))}
        </SidebarDropdown>
      ) : null}
    </List>
  )
}

export default CatalogTree
