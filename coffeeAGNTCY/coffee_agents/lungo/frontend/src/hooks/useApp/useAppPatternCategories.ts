/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { isRequestCancelledError } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import {
  fetchPatternCategories,
  PATTERN_CATEGORIES_LOG_PATH,
  type PatternCategory,
} from "@/utils/agenticWorkflowsApi"

export function useAppPatternCategories() {
  const [patternCategories, setPatternCategories] = useState<
    PatternCategory[] | null
  >(null)
  const [patternCategoriesError, setPatternCategoriesError] = useState<
    string | null
  >(null)

  useEffect(() => {
    const controller = new AbortController()
    setPatternCategoriesError(null)
    fetchPatternCategories(controller.signal)
      .then((items) => {
        setPatternCategories(items)
      })
      .catch((err: unknown) => {
        if (isRequestCancelledError(err)) return
        const httpError = reportRequestError(PATTERN_CATEGORIES_LOG_PATH, err)
        setPatternCategoriesError(httpError.message)
      })
    return () => controller.abort()
  }, [])

  return { patternCategories, patternCategoriesError }
}
