/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Retrying wrappers for the two graph bootstrap requests.
 *
 * The two steps retry independently rather than as a pair. Replaying the pair
 * would re-POST an instantiate that already succeeded, and that endpoint mints a
 * new instance on every call. Budgets and rationale live in
 * `@/config/requestRetryPolicy`.
 */

import {
  getWorkflowInstanceState,
  instantiateWorkflow,
} from "@/api/agenticWorkflowsClient"
import type {
  InstantiateWorkflowResponseWire,
  WorkflowInstanceWire,
} from "@/api/agenticWorkflowsTypes"
import {
  WORKFLOW_INSTANCE_STATE_MAX_RETRIES,
  WORKFLOW_INSTANCE_STATE_RETRY_DELAYS_MS,
  WORKFLOW_INSTANTIATE_MAX_RETRIES,
  WORKFLOW_INSTANTIATE_RETRY_DELAYS_MS,
  WORKFLOW_INSTANTIATE_RETRY_STATUSES,
} from "@/config/requestRetryPolicy"
import {
  hasRetryableStatus,
  isRetryableError,
  isTransportFailureError,
  sleepMs,
} from "@/utils/retryUtils"

type RequestRetryOptions = {
  maxRetries: number
  delaysMs: readonly number[]
  isRetryable: (error: unknown) => boolean
  signal?: AbortSignal
}

async function withRequestRetry<T>(
  operation: () => Promise<T>,
  { maxRetries, delaysMs, isRetryable, signal }: RequestRetryOptions,
): Promise<T> {
  let lastError: unknown

  for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
    try {
      return await operation()
    } catch (error) {
      lastError = error
      const isFinalAttempt = attempt === maxRetries
      if (isFinalAttempt || signal?.aborted || !isRetryable(error)) {
        throw error
      }
      const delayMs = delaysMs[attempt] ?? delaysMs[delaysMs.length - 1]
      await sleepMs(delayMs, signal)
    }
  }

  throw lastError
}

/**
 * Step 1: create the workflow instance.
 *
 * Only replayed when the POST provably never reached the handler, because a
 * duplicate that does reach it leaves an orphan instance the client cannot
 * delete: the id lives in the response it never saw. A 504 is therefore a hard
 * failure here, not a retry, since the handler has already queued the seed
 * event by the time it gives up waiting for the merge.
 */
export function instantiateWorkflowWithRetry(
  baseUrl: string,
  workflowName: string,
  signal?: AbortSignal,
): Promise<InstantiateWorkflowResponseWire> {
  return withRequestRetry(
    () => instantiateWorkflow(baseUrl, workflowName, signal),
    {
      maxRetries: WORKFLOW_INSTANTIATE_MAX_RETRIES,
      delaysMs: WORKFLOW_INSTANTIATE_RETRY_DELAYS_MS,
      isRetryable: (error) =>
        isTransportFailureError(error) ||
        hasRetryableStatus(error, WORKFLOW_INSTANTIATE_RETRY_STATUSES),
      signal,
    },
  )
}

/**
 * Step 2: read the instance topology. Idempotent, so it uses the standard
 * retryable-error rule and never re-runs step 1.
 */
export function getWorkflowInstanceTopologyWithRetry(
  baseUrl: string,
  workflowName: string,
  instancePathUuid: string,
  signal?: AbortSignal,
): Promise<WorkflowInstanceWire> {
  return withRequestRetry(
    () =>
      getWorkflowInstanceState(
        baseUrl,
        workflowName,
        instancePathUuid,
        true,
        signal,
      ),
    {
      maxRetries: WORKFLOW_INSTANCE_STATE_MAX_RETRIES,
      delaysMs: WORKFLOW_INSTANCE_STATE_RETRY_DELAYS_MS,
      isRetryable: isRetryableError,
      signal,
    },
  )
}
