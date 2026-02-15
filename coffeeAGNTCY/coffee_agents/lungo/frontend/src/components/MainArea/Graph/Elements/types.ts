export interface ExtraHandle {
  id: string
  type: "source" | "target"
  position: "top" | "bottom" | "left" | "right"
}

export interface CustomNodeData {
  onOpenOasfModal: HTMLDivElement | null
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
  farmName?: string
  isModalOpen?: boolean
  hasBadgeDetails?: boolean
  hasPolicyDetails?: boolean
  onOpenIdentityModal?: (
    nodeData: any,
    position: { x: number; y: number },
    nodeName?: string,
    data?: any,
    isMcpServer?: boolean,
  ) => void
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
