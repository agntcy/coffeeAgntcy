/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useGroupSessionId } from "@/stores/groupStreamingStore"
import { useStreamingSessionId } from "@/stores/auctionStreamingStore"
import {
  useRecruiterStreamingSessionId,
  useRecruiterTraceId,
} from "@/stores/recruiterStreamingStore"

/**
 * Resolves the OTEL/ioa_observe session id for Grafana deep-linking,
 * regardless of which chat pattern produced the current turn.
 */
export function useObservabilitySessionId(
  agentResponseSessionId?: string,
  agentResponseTraceId?: string,
): string | null {
  const groupSessionId = useGroupSessionId()
  const auctionSessionId = useStreamingSessionId()
  const recruiterSessionId = useRecruiterStreamingSessionId()
  const recruiterTraceId = useRecruiterTraceId()
  return (
    agentResponseTraceId ??
    recruiterTraceId ??
    groupSessionId ??
    auctionSessionId ??
    agentResponseSessionId ??
    recruiterSessionId ??
    null
  )
}
