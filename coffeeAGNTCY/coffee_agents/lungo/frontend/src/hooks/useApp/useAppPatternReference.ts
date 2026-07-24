/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useEffect, useMemo, useState } from "react"
import { v4 as uuid } from "uuid"
import { CanvasMode, type PatternDocState } from "@/types/patternDoc"
import {
  fetchWorkflowDocumentation,
  WorkflowDocumentationNotFoundError,
} from "@/utils/agenticWorkflowsApi"
import { reportRequestError } from "@/errors/request"
import { buildAgenticWorkflowsDocumentationRequest } from "@/urls"

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
    fetchWorkflowDocumentation(selectedReferencePattern, controller.signal)
      .then((doc) => {
        if (controller.signal.aborted) return
        setPatternDocState({
          status: "ready",
          documentation: doc,
          errorMessage: null,
        })
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        if (err instanceof WorkflowDocumentationNotFoundError) {
          setPatternDocState({
            status: "not_found",
            documentation: null,
            errorMessage: null,
          })
        } else {
          const httpError = reportRequestError(
            buildAgenticWorkflowsDocumentationRequest(selectedReferencePattern)
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
