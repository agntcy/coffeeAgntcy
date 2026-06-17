/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Map chat stream authors / sequence steps to React Flow graph element ids.
 */

import type { GraphConfig } from "@/utils/graphConfigs"
import { NODE_IDS } from "@/utils/const"
import { buildSenderToNodeMap } from "./groupCommunicationFeedMapping"

function normalizeAuthor(value: string): string {
  return value.trim().toLowerCase()
}

/** Known recruiter / directory author strings from the discovery stream. */
const AUTHOR_ALIASES: Readonly<Record<string, string>> = {
  recruiter_service: NODE_IDS.RECRUITER,
  recruiter_supervisor: NODE_IDS.RECRUITER,
  recruiteragent: NODE_IDS.RECRUITER,
  "agentic recruiter": NODE_IDS.RECRUITER,
  "agntcy agent directory": NODE_IDS.DIRECTORY,
  directory: NODE_IDS.DIRECTORY,
}

/**
 * Resolve a stream event author to a graph node id using live graph labels and
 * recruiter-specific aliases.
 */
export function resolveStreamAuthorToNodeId(
  author: string | undefined,
  graphConfig?: GraphConfig,
): string | null {
  if (!author?.trim()) return null

  const normalized = normalizeAuthor(author)
  const alias = AUTHOR_ALIASES[normalized]
  if (alias) return alias

  const labelMap = buildSenderToNodeMap(graphConfig)
  return labelMap[author] ?? labelMap[normalized] ?? null
}

/** Highlight ids for the Nth auction stream chunk (0-based). */
export function animationSequenceStepIds(
  graphConfig: GraphConfig | undefined,
  stepIndex: number,
): readonly string[] {
  const step = graphConfig?.animationSequence?.[stepIndex]
  return step?.ids ?? []
}
