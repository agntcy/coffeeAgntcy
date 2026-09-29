/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Single source for HTTP retry budgets, backoff delays, and request timeouts.
 *
 * Values differ per feature by design: UI-blocking requests retry briefly,
 * background refreshes stay quiet, stream reconnects retry longest. Timeouts
 * follow the handler's own bound, not one global number.
 *
 * Shared across all of them: `isRetryableError` in `@/utils/retryUtils`. Retry
 * 5xx, 429, and transport failures; never a 4xx, which answers the same every
 * time.
 */

/**
 * Control-plane JSON calls: catalog, instantiate, instance state, identity,
 * directory.
 *
 * Sized for the slowest of them: instantiate waits on `store.wait_merge_idle`
 * (5s server-side) before returning 504. The 60s `httpFetch` default stays high
 * for LLM chat and streaming, so these opt down instead.
 */
export const CONTROL_PLANE_REQUEST_TIMEOUT_MS = 10_000

/**
 * Graph bootstrap step 1: `POST /agentic-workflows/{name}/`.
 *
 * Not idempotent - every POST mints a new instance uuid, and a replay the
 * server received leaks an instance whose id the client never saw. Only
 * failures that prove the request did not land are retried.
 */
export const WORKFLOW_INSTANTIATE_MAX_RETRIES = 2

/** Clears a container restart without feeling hung. */
export const WORKFLOW_INSTANTIATE_RETRY_DELAYS_MS = [500, 1_500] as const

/**
 * Statuses that mean the request never reached the handler, so a replay cannot
 * duplicate an instance. 503 is the store still starting up, 502 the same
 * behind an ingress. 504 is excluded: the seed event is already queued by then.
 * No-status failures are covered by `isTransportFailureError`.
 */
export const WORKFLOW_INSTANTIATE_RETRY_STATUSES: readonly number[] = [502, 503]

/**
 * Graph bootstrap step 2: `GET /agentic-workflows/{name}/instances/{uuid}/`.
 * Idempotent, so it retries on its own rather than replaying step 1.
 */
export const WORKFLOW_INSTANCE_STATE_MAX_RETRIES = 2

/** Mirrors the instantiate delays to keep the bootstrap window predictable. */
export const WORKFLOW_INSTANCE_STATE_RETRY_DELAYS_MS = [500, 1_500] as const

/** Catalog blocks the sidebar and graph, so it fails fast: 3 tries in ~1.5s. */
export const WORKFLOW_CATALOG_MAX_RETRIES = 2
export const WORKFLOW_CATALOG_RETRY_DELAY_MS = 750

/** Collapses a burst of SSE events for one instance into a single refetch. */
export const TOPOLOGY_REFETCH_DEBOUNCE_MS = 80

/**
 * Topology refetch. The previous graph stays on screen and the next event
 * reschedules anyway, so the budget is small and sub-second.
 */
export const TOPOLOGY_REFETCH_MAX_RETRIES = 2
export const TOPOLOGY_REFETCH_RETRY_DELAYS_MS = [200, 500] as const

/**
 * SSE reconnects, the most generous budget here: losing the stream leaves the
 * graph silently stale, while reconnecting costs one request. Linear backoff
 * (attempt N waits N x the base) spreads 6 attempts over ~5.25s.
 *
 * Counted **per outage** - the counter resets on the next frame, or unrelated
 * blips would accumulate and declare a healthy stream dead.
 */
export const SSE_RECONNECT_MAX_ATTEMPTS = 6
export const SSE_RECONNECT_BACKOFF_MS = 250

/**
 * Chat prompts (`withRetry`). Failures behind an LLM are slow and expensive to
 * repeat, so 1s/2s/4s keeps pressure off a struggling backend while the chat
 * shows a "Retrying..." message.
 */
export const CHAT_RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1_000,
  backoffMultiplier: 2,
} as const

/**
 * The curve above as the delay-per-retry list every other budget here uses.
 * Derived rather than written out so the retry loop and the "Retrying..."
 * countdown in the chat can never quote different numbers.
 */
export const CHAT_RETRY_DELAYS_MS: readonly number[] = Array.from(
  { length: CHAT_RETRY_CONFIG.maxRetries },
  (_, index) =>
    CHAT_RETRY_CONFIG.baseDelay * CHAT_RETRY_CONFIG.backoffMultiplier ** index,
)

/**
 * Suggested prompts are additive UI, so they retry slowly in the background.
 * The delay is flat, not exponential: `getRetryDelayMs` caps `base * 2^n` at a
 * cap equal to the base. Kept as-is; raise the cap to get real backoff.
 */
export const SUGGESTED_PROMPTS_MAX_RETRIES = 3
export const SUGGESTED_PROMPTS_RETRY_BASE_DELAY_MS = 5_000
export const SUGGESTED_PROMPTS_RETRY_MAX_DELAY_MS = 5_000
