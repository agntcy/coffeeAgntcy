/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { reportRequestError } from "@/errors/request"
import {
  fetchPatternCategories,
  type PatternCategory,
} from "@/utils/agenticWorkflowsApi"
import { buildPatternCategoriesRequest } from "@/urls"

export function useAppPatternCategories() {
  const [patternCategories, setPatternCategories] = useState<
    PatternCategory[] | null
  >(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchPatternCategories(controller.signal)
      .then((items) => {
        setPatternCategories(items)
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        reportRequestError(buildPatternCategoriesRequest().endpointLabel, err)
      })
    return () => controller.abort()
  }, [])

  return { patternCategories }
}
