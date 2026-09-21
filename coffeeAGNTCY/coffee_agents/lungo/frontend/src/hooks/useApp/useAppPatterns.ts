/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useState } from "react"
import { isRequestCancelledError } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import {
  fetchPatterns,
  PATTERNS_LOG_PATH,
  type Pattern,
} from "@/utils/patternLibraryApi"

export function useAppPatterns() {
  const [patterns, setPatterns] = useState<Pattern[] | null>(null)
  const [patternsLoading, setPatternsLoading] = useState(true)
  const [patternsError, setPatternsError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setPatternsLoading(true)
    setPatternsError(null)
    fetchPatterns(controller.signal)
      .then((items) => {
        if (controller.signal.aborted) return
        setPatterns(items)
        setPatternsLoading(false)
      })
      .catch((err: unknown) => {
        if (isRequestCancelledError(err)) return
        const httpError = reportRequestError(PATTERNS_LOG_PATH, err)
        setPatternsError(httpError.message)
        setPatternsLoading(false)
      })
    return () => controller.abort()
  }, [])

  return { patterns, patternsLoading, patternsError }
}
