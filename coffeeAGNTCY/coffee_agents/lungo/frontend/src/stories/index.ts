/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { PatternType } from "@/utils/patternUtils"
import { PATTERNS } from "@/utils/patternUtils"
import type { Story } from "./types"
import { coffeeInventoryStory } from "./publishSubscribeStreaming/coffeeInventory"
import { recruiterTourStory } from "./onDemandDiscovery/recruiterTour"

export const storyRegistry: Partial<Record<PatternType, Story[]>> = {
  [PATTERNS.PUBLISH_SUBSCRIBE_STREAMING]: [coffeeInventoryStory],
  [PATTERNS.ON_DEMAND_DISCOVERY]: [recruiterTourStory],
}
