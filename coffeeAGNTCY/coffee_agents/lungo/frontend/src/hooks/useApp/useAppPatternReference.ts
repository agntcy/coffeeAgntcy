/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useEffect, useMemo, useState } from "react"
import { v4 as uuid } from "uuid"
import { CanvasMode, type PatternDocState } from "@/types/patternDoc"
import {
  fetchPatternDocumentation,
  PatternDocumentationNotFoundError,
} from "@/utils/patternLibraryApi"
import { reportRequestError } from "@/errors/request"
import { buildPatternDocumentationRequest } from "@/urls"

export function useAppPatternReference() {
  const [selectedReferencePattern, setSelectedReferencePattern] = useState<
    string | null
  >(null)
  const [patternChatSessionId, setPatternChatSessionId] = useState<
    string | null
  >(null)
  const [patternDocState, setPatternDocState] = useState<PatternDocState>({
    status: "idle",
    documentation: null,
    errorMessage: null,
  })

  const canvasMode: CanvasMode = useMemo(
    () =>
      selectedReferencePattern !== null
        ? CanvasMode.PATTERN_DOC
        : CanvasMode.WORKFLOW,
    [selectedReferencePattern],
  )

  const selectReferencePattern = useCallback((patternName: string | null) => {
    setSelectedReferencePattern(patternName)
    if (patternName !== null) {
      setPatternChatSessionId(`session://${uuid()}`)
    } else {
      setPatternChatSessionId(null)
      setPatternDocState({
        status: "idle",
        documentation: null,
        errorMessage: null,
      })
    }
  }, [])

  useEffect(() => {
    if (selectedReferencePattern === null) return
    const controller = new AbortController()
    setPatternDocState({
      status: "loading",
      documentation: null,
      errorMessage: null,
    })
    fetchPatternDocumentation(selectedReferencePattern, controller.signal)
      .then((doc) => {
        if (controller.signal.aborted) return
        setPatternDocState({
          status: "ready",
          documentation: {
            name: doc.name,
            title: doc.title,
            pattern_category: doc.pattern_category,
            full_markdown: doc.full_markdown,
          },
          errorMessage: null,
        })
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        if (err instanceof PatternDocumentationNotFoundError) {
          setPatternDocState({
            status: "not_found",
            documentation: null,
            errorMessage: null,
          })
        } else {
          const httpError = reportRequestError(
            buildPatternDocumentationRequest(selectedReferencePattern)
              .endpointLabel,
            err,
          )
          setPatternDocState({
            status: "error",
            documentation: null,
            errorMessage: httpError.message,
          })
        }
      })
    return () => controller.abort()
  }, [selectedReferencePattern])

  return {
    selectedReferencePattern,
    setSelectedReferencePattern,
    patternChatSessionId,
    setPatternChatSessionId,
    patternDocState,
    canvasMode,
    selectReferencePattern,
  }
}
