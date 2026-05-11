/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import {
  mapWorkflowNameToSlug,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import type { PatternNode } from "@/utils/sidebarHierarchy"
import { cn } from "@/utils/cn"
import SidebarItem from "./sidebarItem"
import SidebarDropdown from "./SidebarDropdown"
import UseCaseDropdown from "./UseCaseDropdown"
import { makePatternKey, makeScenarioKey } from "./sidebarKeys"

interface CatalogTreeProps {
  tree: PatternNode[]
  expanded: Set<string>
  onToggle: (key: string) => void
  selectedWorkflowSummary: WorkflowSummary | null
  onSelectWorkflow: (summary: WorkflowSummary) => void
}

/**
 * Renders the `pattern -> use-case+scenario -> workflow` tree built from the
 * agentic workflows catalog. Leaf rows are clickable when the workflow name
 * maps to a known Lungo `PatternType`.
 */
const CatalogTree: React.FC<CatalogTreeProps> = ({
  tree,
  expanded,
  onToggle,
  selectedWorkflowSummary,
  onSelectWorkflow,
}) => {
  if (tree.length === 0) {
    return <SidebarItem title="No workflows available" className="opacity-60" />
  }

  return (
    <>
      {tree.map((pattern) => {
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
                  {ucs.workflows.map((workflow) => {
                    const { summary } = workflow
                    const isUnmapped =
                      mapWorkflowNameToSlug(summary.name) === null
                    const isSelected =
                      selectedWorkflowSummary?.name === summary.name
                    return (
                      <SidebarItem
                        key={summary.name}
                        title={summary.name}
                        isSelected={isSelected}
                        onClick={
                          isUnmapped
                            ? undefined
                            : () => onSelectWorkflow(summary)
                        }
                        className={cn(
                          "pl-10",
                          isUnmapped &&
                            "pointer-events-none cursor-not-allowed opacity-50",
                        )}
                      />
                    )
                  })}
                </UseCaseDropdown>
              )
            })}
          </SidebarDropdown>
        )
      })}
    </>
  )
}

export default CatalogTree
