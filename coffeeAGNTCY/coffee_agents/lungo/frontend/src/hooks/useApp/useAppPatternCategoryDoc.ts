/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { isRequestCancelledError } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import { type PatternDocState } from "@/types/patternDoc"
import { buildPatternCategoryDocumentationRequest } from "@/urls"
import {
  fetchPatternCategoryDocumentation,
  PatternCategoryDocumentationNotFoundError,
  patternCategoryBodyMarkdown,
} from "@/utils/agenticWorkflowsApi"

const idleCategoryDocState: PatternDocState = {
  status: "idle",
  documentation: null,
  errorMessage: null,
}

export function useAppPatternCategoryDoc(
  selectedPatternCategory: string | null,
) {
  const [categoryDocState, setCategoryDocState] =
    useState<PatternDocState>(idleCategoryDocState)

  useEffect(() => {
    if (selectedPatternCategory === null) {
      setCategoryDocState(idleCategoryDocState)
      return
    }

    const controller = new AbortController()
    setCategoryDocState({
      status: "loading",
      documentation: null,
      errorMessage: null,
    })

    fetchPatternCategoryDocumentation(
      selectedPatternCategory,
      controller.signal,
    )
      .then((doc) => {
        if (controller.signal.aborted) return
        setCategoryDocState({
          status: "ready",
          documentation: {
            workflow_name: doc.slug,
            title: doc.title ?? doc.name,
            pattern_category: doc.name,
            full_markdown: patternCategoryBodyMarkdown(doc.full_markdown),
          },
          errorMessage: null,
        })
      })
      .catch((err: unknown) => {
        if (isRequestCancelledError(err)) return
        if (err instanceof PatternCategoryDocumentationNotFoundError) {
          setCategoryDocState({
            status: "not_found",
            documentation: null,
            errorMessage: null,
          })
          return
        }
        const httpError = reportRequestError(
          buildPatternCategoryDocumentationRequest(selectedPatternCategory)
            .endpointLabel,
          err,
        )
        setCategoryDocState({
          status: "error",
          documentation: null,
          errorMessage: httpError.message,
        })
      })

    return () => controller.abort()
  }, [selectedPatternCategory])

  return { categoryDocState }
}
