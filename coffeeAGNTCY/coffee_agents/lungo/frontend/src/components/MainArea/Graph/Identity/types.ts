import { CustomNodeData } from "../Elements/types"

export interface PolicyData {
  policies: Array<{
    id: string
    name: string
    description: string
    assignedTo: string
    rules: Array<{
      id: string
      name: string
      description: string
      tasks: any[]
      action: string
      needsApproval: boolean
      createdAt: string
    }>
    createdAt: string
  }>
}

export interface IdentityModalProps {
  isOpen: boolean
  onClose: () => void
  onShowBadgeDetails: () => void
  onShowPolicyDetails: () => void
  nodeName: string
  position: { x: number; y: number }
  activeModal?: string | null
  nodeData?: CustomNodeData
  isMcpServer?: boolean
}
export interface BadgeData {
  context: string[]
  type: string[]
  issuer: string
  credentialSubject: {
    id: string
    badge: string
  }
  id: string
  issuanceDate: string
  expirationDate: string
  credentialSchema: any[]
  credentialStatus: any[]
  proof: {
    type: string
    proofPurpose: string
    proofValue: string
  }
  badge: {
    capabilities: {
      streaming: boolean
    }
    defaultInputModes: string[]
    defaultOutputModes: string[]
    description: string
    name: string
    preferredTransport: string
    protocolVersion: string
    security: Array<{
      IdentityServiceAuthScheme: string[]
    }>
    securitySchemes: {
      IdentityServiceAuthScheme: {
        bearerFormat: string
        scheme: string
        type: string
      }
    }
    skills: Array<{
      description: string
      examples: string[]
      id: string
      name: string
      tags: string[]
    }>
    supportsAuthenticatedExtendedCard: boolean
    url: string
    version: string
  }
}
