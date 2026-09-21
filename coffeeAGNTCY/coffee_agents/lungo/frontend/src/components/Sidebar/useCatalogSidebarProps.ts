/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Adapts the app state into sidebar props. The workflow catalog and the pattern
 * reference library load independently, so both their rows and their errors are
 * forwarded separately.
 **/

import { useMemo } from "react"
import type { useApp } from "@/useApp"
import type { SidebarProps } from "./Sidebar"

export function useCatalogSidebarProps(
  app: ReturnType<typeof useApp>,
): SidebarProps {
  const {
    selectedWorkflowSummary,
    workflowCatalogSummaries,
    workflowCatalogLoading,
    workflowCatalogError,
    patterns,
    patternsLoading,
    patternsError,
    patternCategories,
    patternCategoriesError,
    selectWorkflowFromCatalog,
    selectedReferencePattern,
    selectReferencePattern,
    selectedPatternCategory,
    selectPatternCategory,
  } = app

  return useMemo(
    () => ({
      selectedWorkflowSummary,
      summaries: workflowCatalogSummaries,
      patterns,
      patternsLoading,
      patternsError,
      patternCategories,
      patternCategoriesError,
      isLoading: workflowCatalogLoading,
      error: workflowCatalogError,
      onSelectWorkflow: selectWorkflowFromCatalog,
      selectedReferencePattern,
      onSelectReferencePattern: selectReferencePattern,
      selectedPatternCategory,
      onSelectPatternCategory: selectPatternCategory,
    }),
    [
      selectedWorkflowSummary,
      workflowCatalogSummaries,
      patterns,
      patternsLoading,
      patternsError,
      patternCategories,
      patternCategoriesError,
      workflowCatalogLoading,
      workflowCatalogError,
      selectWorkflowFromCatalog,
      selectedReferencePattern,
      selectReferencePattern,
      selectedPatternCategory,
      selectPatternCategory,
    ],
  )
}
