/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { PatternType } from "@/utils/patternUtils"
import type { CatalogSidebarEntry, PatternNode } from "@/utils/sidebarHierarchy"
import { cn } from "@/utils/cn"
import SidebarItem from "./sidebarItem"
import SidebarDropdown from "./SidebarDropdown"
import UseCaseDropdown from "./UseCaseDropdown"
import { makePatternKey, makeScenarioKey } from "./sidebarKeys"

interface CatalogTreeProps {
  tree: CatalogSidebarEntry[]
  expanded: Set<string>
  onToggle: (key: string) => void
  selectedPattern: PatternType
  onPatternChange: (pattern: PatternType) => void
}

/**
 * Renders the `pattern -> use-case+scenario -> workflow` tree built from the
 * agentic workflows catalog. Patterns and use-case rows are collapsible; leaf
 * workflow rows are clickable when their slug maps to a known `PatternType`.
 */
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
      {tree.map((entry, index) => {
        if (entry.kind === "separator") {
          return (
            <div
              key={`catalog-separator-${index}`}
              className="my-2 border-t border-sidebar-border px-2"
              role="separator"
              aria-hidden="true"
            />
          )
        }

        const pattern: PatternNode = entry.node
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
                            : () => onPatternChange(workflow.slug!)}
                        className={cn(
                          "pl-10",
                          isUnknown &&
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
