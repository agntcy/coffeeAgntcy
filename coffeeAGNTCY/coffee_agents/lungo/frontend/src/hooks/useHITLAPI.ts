/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Human-in-the-Loop (HITL) API Hook
 *
 * This hook provides methods to interact with the HITL endpoints:
 * - sendHITLPrompt: Sends a prompt that may trigger human intervention
 * - resumeHITL: Resumes an interrupted request with human's decision
 */

import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { getApiUrlForPattern } from "@/utils/patternUtils"
import { isLocalDev } from "@/utils/const"

// Types for HITL API responses
export interface HITLScenario {
  name: string
  description: string
  farm_allocations: Record<string, number>
  total_cost: number
  quality_score: number
  risk_level: string
}

export interface TriggerModelOutput {
  name: string
  description: string
  decision: string
  confidence: number
  reasons: string[]
}

export interface RespondModelOutput {
  name: string
  description: string
  summary: string
  scenarios: HITLScenario[]
  recommendation: string
  rationale: string
}

export interface HITLInterrupt {
  type: string
  // Model outputs - explicitly show both models
  trigger_model: TriggerModelOutput
  respond_model: RespondModelOutput
  // Legacy fields for backwards compatibility
  summary: string
  scenarios: HITLScenario[]
  recommendation: string
  rationale: string
  instructions: string
}

export interface HITLResponse {
  status: "completed" | "awaiting_human_input" | "error"
  response: string | null
  interrupt: HITLInterrupt | null
  thread_id: string
}

export interface UseHITLAPIReturn {
  loading: boolean
  hitlState: HITLResponse | null
  sendHITLPrompt: (prompt: string, pattern?: string) => Promise<HITLResponse>
  resumeHITL: (
    threadId: string,
    decision: string,
    pattern?: string
  ) => Promise<HITLResponse>
  resetHITL: () => void
  cancel: () => void
}

export const useHITLAPI = (): UseHITLAPIReturn => {
  const [loading, setLoading] = useState<boolean>(false)
  const [hitlState, setHitlState] = useState<HITLResponse | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const cancel = () => {
    if (abortRef.current) {
      abortRef.current.abort()
    }
  }

  const resetHITL = () => {
    setHitlState(null)
  }

  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort()
      }
    }
  }, [])

  /**
   * Send a prompt to the HITL endpoint
   * If the system needs human intervention, it returns with status="awaiting_human_input"
   */
  const sendHITLPrompt = async (
    prompt: string,
    pattern?: string
  ): Promise<HITLResponse> => {
    if (!prompt.trim()) {
      throw new Error("Prompt cannot be empty")
    }

    const apiUrl = getApiUrlForPattern(pattern)
    setLoading(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await axios.post<HITLResponse>(
        `${apiUrl}/agent/prompt/hitl`,
        { prompt },
        {
          signal: controller.signal,
          withCredentials: !isLocalDev,
        }
      )

      setHitlState(response.data)
      return response.data
    } finally {
      setLoading(false)
    }
  }

  /**
   * Resume an interrupted HITL request with the human's decision
   */
  const resumeHITL = async (
    threadId: string,
    decision: string,
    pattern?: string
  ): Promise<HITLResponse> => {
    if (!threadId || !decision.trim()) {
      throw new Error("Thread ID and decision are required")
    }

    const apiUrl = getApiUrlForPattern(pattern)
    setLoading(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await axios.post<HITLResponse>(
        `${apiUrl}/agent/prompt/hitl/resume`,
        {
          thread_id: threadId,
          decision: decision,
        },
        {
          signal: controller.signal,
          withCredentials: !isLocalDev,
        }
      )

      setHitlState(response.data)
      return response.data
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    hitlState,
    sendHITLPrompt,
    resumeHITL,
    resetHITL,
    cancel,
  }
}
