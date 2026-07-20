/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { reportRequestError } from "@/errors/request"
import {
  AGENTIC_WORKFLOWS_CATALOG_LOG_PATH,
  fetchWorkflowSummariesWithRetry,
  pickDefaultWorkflowSummaryForPattern,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import { patternTypeFromSummary } from "@/utils/workflow"
import type { PatternType } from "@/utils/patternUtils"

export function useAppWorkflowCatalog(selectedPattern: PatternType) {
  const [workflowCatalogSummaries, setWorkflowCatalogSummaries] = useState<
    WorkflowSummary[] | null
  >(null)
  const [workflowCatalogLoading, setWorkflowCatalogLoading] = useState(true)
  const [workflowCatalogError, setWorkflowCatalogError] = useState<
    string | null
  >(null)
  const [selectedWorkflowSummary, setSelectedWorkflowSummary] =
    useState<WorkflowSummary | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setWorkflowCatalogLoading(true)
    setWorkflowCatalogError(null)
    fetchWorkflowSummariesWithRetry(controller.signal)
      .then((rows) => {
        setWorkflowCatalogSummaries(rows)
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        const httpError = reportRequestError(
          AGENTIC_WORKFLOWS_CATALOG_LOG_PATH,
          err,
        )
        setWorkflowCatalogError(httpError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setWorkflowCatalogLoading(false)
        }
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (workflowCatalogSummaries === null) return
    setSelectedWorkflowSummary((prev) => {
      if (prev) {
        const still = workflowCatalogSummaries.find((s) => s.name === prev.name)
        if (still && patternTypeFromSummary(still) === selectedPattern) {
          return still
        }
      }
      return pickDefaultWorkflowSummaryForPattern(
        workflowCatalogSummaries,
        selectedPattern,
      )
    })
  }, [workflowCatalogSummaries, selectedPattern])

  return {
    workflowCatalogSummaries,
    workflowCatalogLoading,
    workflowCatalogError,
    selectedWorkflowSummary,
    setSelectedWorkflowSummary,
  }
}
