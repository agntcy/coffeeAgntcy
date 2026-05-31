/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback } from "react"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import {
  mapWorkflowNameToSlug,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import { openWorkflowDocumentationInNewTab } from "@/utils/workflowDocumentationGithub"
import SidebarDropdown from "./SidebarDropdown"
import SidebarItem from "./SidebarItem"
import { CatalogTreeLevel } from "./sidebarLevel"
import {
  makePatternKey,
  makeScenarioKey,
  makeUseCaseKey,
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
        level={CatalogTreeLevel.Workflow}
        isSelected={isSelected}
        disabled={isUnmapped}
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
        level={CatalogTreeLevel.Pattern}
        isExpanded={expandedKeys.has(patternKey)}
        onToggle={() => toggleExpandableDropdown(patternKey)}
      >
        {[...byUseCase.entries()].map(([useCase, scenarios]) => {
          const useCaseKey = makeUseCaseKey(pattern.name, useCase)
          return (
            <SidebarDropdown
              key={useCaseKey}
              title={useCase}
              level={CatalogTreeLevel.UseCase}
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
                    level={CatalogTreeLevel.Scenario}
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
    <Stack direction="column" sx={{ width: "100%" }}>
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

      {referencePatternNames.map((patternName) => (
        <SidebarItem
          key={patternName}
          title={patternName}
          level={CatalogTreeLevel.Pattern}
          onClick={() => openDoc(patternName)}
        />
      ))}
    </Stack>
  )
}

export default CatalogTree
