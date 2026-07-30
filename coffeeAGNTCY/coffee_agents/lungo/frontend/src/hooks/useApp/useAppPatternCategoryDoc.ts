/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { reportRequestError } from "@/errors/request"
import { buildPatternCategoryDocumentationRequest } from "@/urls"
import {
  fetchPatternCategoryDocumentation,
  PatternCategoryDocumentationNotFoundError,
  patternCategoryBodyMarkdown,
} from "@/utils/agenticWorkflowsApi"

export function useAppPatternCategoryDoc(selectedPatternCategory: string | null) {
  const [selectedCategoryMarkdown, setSelectedCategoryMarkdown] = useState<
    string | null
  >(null)
  const [selectedCategoryDocLoading, setSelectedCategoryDocLoading] =
    useState(false)
  const [selectedCategoryDocError, setSelectedCategoryDocError] = useState<
    string | null
  >(null)

  useEffect(() => {
    if (selectedPatternCategory === null) {
      setSelectedCategoryMarkdown(null)
      setSelectedCategoryDocLoading(false)
      setSelectedCategoryDocError(null)
      return
    }

    const controller = new AbortController()
    setSelectedCategoryDocLoading(true)
    setSelectedCategoryDocError(null)
    setSelectedCategoryMarkdown(null)

    fetchPatternCategoryDocumentation(
      selectedPatternCategory,
      controller.signal,
    )
      .then((doc) => {
        if (controller.signal.aborted) return
        setSelectedCategoryMarkdown(
          patternCategoryBodyMarkdown(doc.full_markdown),
        )
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        if (err instanceof PatternCategoryDocumentationNotFoundError) {
          setSelectedCategoryMarkdown(null)
          setSelectedCategoryDocError(null)
          return
        }
        const httpError = reportRequestError(
          buildPatternCategoryDocumentationRequest(selectedPatternCategory)
            .endpointLabel,
          err,
        )
        setSelectedCategoryDocError(httpError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setSelectedCategoryDocLoading(false)
        }
      })

    return () => controller.abort()
  }, [selectedPatternCategory])

  return {
    selectedCategoryMarkdown,
    selectedCategoryDocLoading,
    selectedCategoryDocError,
  }
}
