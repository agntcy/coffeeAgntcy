import type { AgentTransport } from "./transportMeta"

export interface ExtraHandle {
  id: string
  type: "source" | "target"
  position: "top" | "bottom" | "left" | "right"
}

export interface CustomNodeData {
  onOpenOasfModal?: (nodeData: CustomNodeData) => void
  icon: React.ReactNode
  label1: string
  label2: string
  active?: boolean
  selected?: boolean
  agentCid?: string
  handles?: "all" | "target" | "source"
  extraHandles?: ExtraHandle[]
  verificationStatus?: "verified" | "failed" | "pending"
  verificationBadge?: React.ReactNode
  githubLink?: string
  agentDirectoryLink?: string
  transportInterfaces?: AgentTransport[]
  activeTransport?: string
  /** Slug for `GET .../identity-apps/{slug}/...` (differs from directory OASF slug for some agents). */
  identityAppsSlug?: string
  /** Slug for `GET .../agents/{slug}/oasf` (AGNTCY Directory / OASF card). */
  directoryAgentSlug?: string
  /** Legacy combined slug; prefer `identityAppsSlug` / `directoryAgentSlug` when set. */
  slug?: string
  farmName?: string
  isModalOpen?: boolean
  /** True when this node's identity dropdown is open. */
  isIdentityDropdownOpen?: boolean
  hasBadgeDetails?: boolean
  hasPolicyDetails?: boolean
  onOpenIdentityModal?: (nodeId: string, nodeData: CustomNodeData) => void
  onCloseIdentityDropdown?: () => void
  onShowBadgeDetails?: () => void
  onShowPolicyDetails?: () => void
}

export interface TransportNodeData {
  label: string
  active?: boolean
  githubLink?: string
  compact?: boolean
}

export interface CustomEdgeData {
  active?: boolean
  label?: string
  labelIconType?: string
}

export interface BranchingEdgeData {
  active?: boolean
  label?: string
  branches?: string[]
}
