/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * `LungoSidebarNavigationSlot` is the single ReactElement passed to `SidebarFrame.navigationItems`;
 * it carries the multi-level menu (headings + `SidebarDropdown`). Only that slot pattern allows
 * arbitrary composed content beside top-level `SidebarRailItem` rows — keep it unless the frame
 * API gains a richer tree prop.
 **/

import React, { useEffect, useMemo, useState } from "react"
import type { SxProps, Theme } from "@mui/material/styles"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import { Podcast, Search, Share2, Users } from "lucide-react"
import {
  PatternType,
  PATTERNS,
  getApiUrlForPattern,
} from "@/utils/patternUtils"
import { logger } from "@/utils/logger"
import SidebarDropdown from "./SidebarDropdown"
import { SidebarFrame } from "./SidebarFrame"
import { SidebarRailRow } from "./SidebarRailRow"

interface LungoSidebarProps {
  selectedPattern: PatternType
  onPatternChange: (pattern: PatternType) => void
}

/** Single source of truth: order defines collapsed rail order and grouping for the expanded tree. */
interface LungoMenuLeaf {
  id: string
  pattern: PatternType
  conversationTitle: string
  dropdownTitle: string
  /** `SidebarSectionHeading` indent for “Agentic Patterns” under this conversation. */
  agenticHeadingPl: number
  icon: React.ReactElement
  getTooltip: (transportLabel: string) => string
  getAriaLabel: (transportLabel: string) => string
}

const LUNGO_MENU_LEAVES: LungoMenuLeaf[] = [
  {
    id: "lungo-pat-gc",
    pattern: PATTERNS.GROUP_COMMUNICATION,
    conversationTitle: "Order Fulfilment",
    dropdownTitle: "Secure Group Communication",
    agenticHeadingPl: 2,
    icon: <Users size={24} aria-hidden />,
    getTooltip: () => "A2A SLIM",
    getAriaLabel: () => "A2A SLIM",
  },
  {
    id: "lungo-pat-ps",
    pattern: PATTERNS.PUBLISH_SUBSCRIBE,
    conversationTitle: "Coffee Buying",
    dropdownTitle: "Publish Subscribe",
    agenticHeadingPl: 2,
    icon: <Share2 size={24} aria-hidden />,
    getTooltip: (t) => `A2A ${t} · Publish Subscribe`,
    getAriaLabel: (t) => `A2A ${t} · Publish Subscribe`,
  },
  {
    id: "lungo-pat-pss",
    pattern: PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
    conversationTitle: "Coffee Buying",
    dropdownTitle: "Publish Subscribe: Streaming",
    agenticHeadingPl: 2,
    icon: <Podcast size={24} aria-hidden />,
    getTooltip: (t) => `A2A ${t} · Streaming`,
    getAriaLabel: (t) => `A2A ${t} · Streaming`,
  },
  {
    id: "lungo-pat-odd",
    pattern: PATTERNS.ON_DEMAND_DISCOVERY,
    conversationTitle: "Capability Discovery",
    dropdownTitle: "Recruiter",
    agenticHeadingPl: 2,
    icon: <Search size={24} aria-hidden />,
    getTooltip: () => "A2A HTTP",
    getAriaLabel: () => "A2A HTTP",
  },
]

function groupLeavesByConversation(
  leaves: LungoMenuLeaf[],
  transportLabel: string,
): Array<{
  conversationTitle: string
  agenticHeadingPl: number
  rows: Array<{
    leaf: LungoMenuLeaf
    tooltip: string
    ariaLabel: string
  }>
}> {
  const order: string[] = []
  const bucket = new Map<
    string,
    {
      conversationTitle: string
      agenticHeadingPl: number
      rows: Array<{
        leaf: LungoMenuLeaf
        tooltip: string
        ariaLabel: string
      }>
    }
  >()

  for (const leaf of leaves) {
    const tooltip = leaf.getTooltip(transportLabel)
    const ariaLabel = leaf.getAriaLabel(transportLabel)
    const key = leaf.conversationTitle
    if (!bucket.has(key)) {
      order.push(key)
      bucket.set(key, {
        conversationTitle: leaf.conversationTitle,
        agenticHeadingPl: leaf.agenticHeadingPl,
        rows: [],
      })
    }
    bucket.get(key)!.rows.push({ leaf, tooltip, ariaLabel })
  }

  return order.map((k) => bucket.get(k)!)
}

interface LungoSidebarNavigationSlotProps {
  iconOnly?: boolean
  selectedPattern: PatternType
  onPatternChange: (pattern: PatternType) => void
  transport: string
  isPublishSubscribeExpanded: boolean
  setIsPublishSubscribeExpanded: React.Dispatch<React.SetStateAction<boolean>>
  isPublishSubscribeStreamingExpanded: boolean
  setIsPublishSubscribeStreamingExpanded: React.Dispatch<
    React.SetStateAction<boolean>
  >
  isGroupCommunicationExpanded: boolean
  setIsGroupCommunicationExpanded: React.Dispatch<React.SetStateAction<boolean>>
  isOnDemandDiscoveryExpanded: boolean
  setIsOnDemandDiscoveryExpanded: React.Dispatch<React.SetStateAction<boolean>>
}

function getDropdownExpandState(
  leafId: string,
  p: Pick<
    LungoSidebarNavigationSlotProps,
    | "isPublishSubscribeExpanded"
    | "setIsPublishSubscribeExpanded"
    | "isPublishSubscribeStreamingExpanded"
    | "setIsPublishSubscribeStreamingExpanded"
    | "isGroupCommunicationExpanded"
    | "setIsGroupCommunicationExpanded"
    | "isOnDemandDiscoveryExpanded"
    | "setIsOnDemandDiscoveryExpanded"
  >,
): { isExpanded: boolean; onToggle: () => void } {
  switch (leafId) {
    case "lungo-pat-gc":
      return {
        isExpanded: p.isGroupCommunicationExpanded,
        onToggle: () => p.setIsGroupCommunicationExpanded((v) => !v),
      }
    case "lungo-pat-ps":
      return {
        isExpanded: p.isPublishSubscribeExpanded,
        onToggle: () => p.setIsPublishSubscribeExpanded((v) => !v),
      }
    case "lungo-pat-pss":
      return {
        isExpanded: p.isPublishSubscribeStreamingExpanded,
        onToggle: () => p.setIsPublishSubscribeStreamingExpanded((v) => !v),
      }
    case "lungo-pat-odd":
      return {
        isExpanded: p.isOnDemandDiscoveryExpanded,
        onToggle: () => p.setIsOnDemandDiscoveryExpanded((v) => !v),
      }
    default:
      return { isExpanded: true, onToggle: () => {} }
  }
}

function LungoSidebarNavigationSlot({
  iconOnly,
  selectedPattern,
  onPatternChange,
  transport,
  ...expandProps
}: LungoSidebarNavigationSlotProps) {
  const transportLabel = transport || "…"
  const railOpen = !iconOnly

  const sections = useMemo(
    () => groupLeavesByConversation(LUNGO_MENU_LEAVES, transportLabel),
    [transportLabel],
  )

  const renderRailRow = (args: {
    leaf: LungoMenuLeaf
    tooltip: string
    ariaLabel: string
  }) => {
    const { leaf, tooltip, ariaLabel } = args
    return (
      <SidebarRailRow
        key={leaf.id}
        id={leaf.id}
        aria-label={ariaLabel}
        tooltip={tooltip}
        icon={leaf.icon}
        railOpen={railOpen}
        selected={selectedPattern === leaf.pattern}
        onClick={() => onPatternChange(leaf.pattern)}
      />
    )
  }

  const collapsedMenu = (
    <Stack spacing={0.5} sx={{ width: "100%", alignItems: "stretch", py: 0.5 }}>
      {LUNGO_MENU_LEAVES.map((leaf) =>
        renderRailRow({
          leaf,
          tooltip: leaf.getTooltip(transportLabel),
          ariaLabel: leaf.getAriaLabel(transportLabel),
        }),
      )}
    </Stack>
  )

  const expandedMenu = (
    <Stack spacing={2.5} sx={innerSx}>
      {sections.map((section) => (
        <Stack key={section.conversationTitle} sx={sectionBlockSx}>
          <SidebarSectionHeading pl={0}>
            {section.conversationTitle}
          </SidebarSectionHeading>

          <Stack sx={sectionBlockSx}>
            <SidebarSectionHeading pl={section.agenticHeadingPl}>
              Agentic Patterns
            </SidebarSectionHeading>

            {section.rows.map(({ leaf, tooltip, ariaLabel }) => {
              const { isExpanded, onToggle } = getDropdownExpandState(
                leaf.id,
                expandProps,
              )
              return (
                <Box key={leaf.id}>
                  <SidebarDropdown
                    title={leaf.dropdownTitle}
                    isExpanded={isExpanded}
                    onToggle={onToggle}
                  >
                    {renderRailRow({ leaf, tooltip, ariaLabel })}
                  </SidebarDropdown>
                </Box>
              )
            })}
          </Stack>
        </Stack>
      ))}
    </Stack>
  )

  return (
    <Box
      component="nav"
      aria-label="Conversation and agentic patterns"
      sx={{
        width: "100%",
        minWidth: 0,
        alignSelf: "stretch",
        ...(iconOnly
          ? {
              display: "flex",
              justifyContent: "center",
            }
          : { flex: 1 }),
      }}
    >
      {iconOnly ? collapsedMenu : expandedMenu}
    </Box>
  )
}

const innerSx: SxProps<Theme> = {
  flex: 1,
  minHeight: 0,
  overflow: "auto",
}

const sectionBlockSx: SxProps<Theme> = {
  display: "flex",
  flexDirection: "column",
}

const headingRowSx = (plKey: number): SxProps<Theme> => ({
  padding: "5px",
  pl: plKey,
})

const headingTextSx: SxProps<Theme> = {
  flex: 1,
  textWrap: "auto",
  fontWeight: 600,
}

function SidebarSectionHeading({
  children,
  pl = 1,
}: {
  children: React.ReactNode
  pl?: number
}) {
  return (
    <Box sx={headingRowSx(pl)}>
      <Typography component="span" variant="body1" sx={headingTextSx}>
        {children}
      </Typography>
    </Box>
  )
}

const Sidebar: React.FC<LungoSidebarProps> = ({
  selectedPattern,
  onPatternChange,
}) => {
  const [isPublishSubscribeExpanded, setIsPublishSubscribeExpanded] =
    useState(true)
  const [
    isPublishSubscribeStreamingExpanded,
    setIsPublishSubscribeStreamingExpanded,
  ] = useState(true)
  const [isGroupCommunicationExpanded, setIsGroupCommunicationExpanded] =
    useState(true)
  const [isOnDemandDiscoveryExpanded, setIsOnDemandDiscoveryExpanded] =
    useState(true)
  const [transport, setTransport] = useState<string>("")

  useEffect(() => {
    const fetchTransportConfig = async () => {
      try {
        const response = await fetch(
          `${getApiUrlForPattern(PATTERNS.PUBLISH_SUBSCRIBE)}/transport/config`,
        )
        const data = await response.json()
        if (data.transport) {
          setTransport(data.transport)
        }
      } catch (error) {
        logger.error("Error fetching transport config:", error)
      }
    }

    fetchTransportConfig()
  }, [])

  return (
    <SidebarFrame
      initialOpen
      navigationItems={[
        <LungoSidebarNavigationSlot
          key="lungo-pattern-nav"
          selectedPattern={selectedPattern}
          onPatternChange={onPatternChange}
          transport={transport}
          isPublishSubscribeExpanded={isPublishSubscribeExpanded}
          setIsPublishSubscribeExpanded={setIsPublishSubscribeExpanded}
          isPublishSubscribeStreamingExpanded={
            isPublishSubscribeStreamingExpanded
          }
          setIsPublishSubscribeStreamingExpanded={
            setIsPublishSubscribeStreamingExpanded
          }
          isGroupCommunicationExpanded={isGroupCommunicationExpanded}
          setIsGroupCommunicationExpanded={setIsGroupCommunicationExpanded}
          isOnDemandDiscoveryExpanded={isOnDemandDiscoveryExpanded}
          setIsOnDemandDiscoveryExpanded={setIsOnDemandDiscoveryExpanded}
        />,
      ]}
    />
  )
}

export default Sidebar
