/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback } from "react"
import { Box, List, Typography } from "@open-ui-kit/core"
import { type WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { patternTypeFromSummary } from "@/utils/workflow"
import { openWorkflowDocumentationInNewTab } from "@/utils/workflowDocumentationGithub"
import SidebarDropdown from "./SidebarDropdown"
import SidebarItem from "./SidebarItem"
import {
  makePatternKey,
  makeReferenceCategoryKey,
  makeScenarioKey,
  makeWorkflowKey,
  A2A_SLIM_MENU_LABEL,
  REFERENCE_LIBRARY_KEY,
  type CatalogSidebarLayout,
  type PatternNode,
  type ReferenceCategoryNode,
  type UseCaseScenarioNode,
  type WorkflowNode,
} from "./sidebar.utils"

interface CatalogTreeProps {
  layout: CatalogSidebarLayout
  expandedKeys: Set<string>
  toggleExpandableDropdown: (key: string) => void
  selectedWorkflowSummary: WorkflowSummary | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
  selectedReferencePattern?: string | null
  onSelectReferencePattern?: (patternName: string) => void
  onSelectPatternCategory?: (categoryName: string) => void
}

const CatalogTree: React.FC<CatalogTreeProps> = ({
  layout,
  expandedKeys,
  toggleExpandableDropdown,
  selectedWorkflowSummary,
  onSelectWorkflow,
  selectedReferencePattern,
  onSelectReferencePattern,
  onSelectPatternCategory,
}) => {
  const { implementedPatterns, referenceCategories } = layout

  const openDoc = useCallback((catalogName: string) => {
    openWorkflowDocumentationInNewTab(catalogName)
  }, [])

  const toggleCategory = useCallback(
    (categoryKey: string, categoryName: string) => {
      toggleExpandableDropdown(categoryKey)
      onSelectPatternCategory?.(categoryName)
    },
    [onSelectPatternCategory, toggleExpandableDropdown],
  )

  const renderWorkflow = useCallback(
    (
      patternName: string,
      ucs: UseCaseScenarioNode,
      workflow: WorkflowNode,
    ): React.ReactNode => {
      const { summary, display } = workflow
      const isUnmapped = patternTypeFromSummary(summary) === null
      const isSelected = selectedWorkflowSummary?.name === summary.name

      if (display === "slim_transport") {
        const workflowKey = makeWorkflowKey(
          patternName,
          ucs.useCase,
          ucs.scenario,
          summary.name,
        )

        return (
          <SidebarDropdown
            key={summary.name}
            title={summary.name}
            isExpanded={expandedKeys.has(workflowKey)}
            onToggle={() => toggleExpandableDropdown(workflowKey)}
          >
            <SidebarItem
              title={A2A_SLIM_MENU_LABEL}
              isSelected={isSelected}
              onClick={isUnmapped ? undefined : () => onSelectWorkflow(summary)}
            />
          </SidebarDropdown>
        )
      }

      return (
        <SidebarItem
          key={summary.name}
          title={summary.name}
          isSelected={isSelected}
          onClick={isUnmapped ? undefined : () => onSelectWorkflow(summary)}
        />
      )
    },
    [
      expandedKeys,
      onSelectWorkflow,
      selectedWorkflowSummary,
      toggleExpandableDropdown,
    ],
  )

  const renderPattern = (pattern: PatternNode): React.ReactNode => {
    const patternKey = makePatternKey(pattern.name)

    return (
      <SidebarDropdown
        key={patternKey}
        title={pattern.name}
        isExpanded={expandedKeys.has(patternKey)}
        onToggle={() => toggleExpandableDropdown(patternKey)}
      >
        {pattern.useCaseScenarios.map((scenario: UseCaseScenarioNode) => {
          const scenarioKey = makeScenarioKey(
            pattern.name,
            scenario.useCase,
            scenario.scenario,
          )
          return (
            <SidebarDropdown
              key={scenarioKey}
              title={scenario.label}
              isExpanded={expandedKeys.has(scenarioKey)}
              onToggle={() => toggleExpandableDropdown(scenarioKey)}
            >
              {scenario.workflows.map((wf: WorkflowNode) =>
                renderWorkflow(pattern.name, scenario, wf),
              )}
            </SidebarDropdown>
          )
        })}
      </SidebarDropdown>
    )
  }

  const renderReferenceCategory = (
    category: ReferenceCategoryNode,
  ): React.ReactNode => {
    const categoryKey = makeReferenceCategoryKey(category.name)

    return (
      <SidebarDropdown
        key={categoryKey}
        title={category.name}
        isExpanded={expandedKeys.has(categoryKey)}
        onToggle={() => toggleCategory(categoryKey, category.name)}
      >
        {category.patternNames.map((patternName) => (
          <SidebarItem
            key={patternName}
            title={patternName}
            isSelected={selectedReferencePattern === patternName}
            onClick={
              onSelectReferencePattern
                ? () => onSelectReferencePattern(patternName)
                : () => openDoc(patternName)
            }
          />
        ))}
      </SidebarDropdown>
    )
  }

  const hasImplemented = implementedPatterns.length > 0
  const hasReference = referenceCategories.some(
    (category) => category.patternNames.length > 0,
  )

  if (!hasImplemented && !hasReference) {
    return (
      <Typography variant="body2" sx={{ px: 2.5, py: 1, opacity: 0.6 }}>
        No workflows available
      </Typography>
    )
  }

  const showSeparator = hasImplemented && hasReference

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

      {hasReference ? (
        <SidebarDropdown
          title="Reference Library"
          isExpanded={expandedKeys.has(REFERENCE_LIBRARY_KEY)}
          onToggle={() => toggleExpandableDropdown(REFERENCE_LIBRARY_KEY)}
        >
          {referenceCategories.map(renderReferenceCategory)}
        </SidebarDropdown>
      ) : null}
    </List>
  )
}

export default CatalogTree
