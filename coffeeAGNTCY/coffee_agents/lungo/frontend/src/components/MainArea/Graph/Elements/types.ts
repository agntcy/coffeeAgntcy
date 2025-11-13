export interface CustomNodeData {
  icon: React.ReactNode
  label1: string
  label2: string
  active?: boolean
  handles?: "all" | "target" | "source"
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
