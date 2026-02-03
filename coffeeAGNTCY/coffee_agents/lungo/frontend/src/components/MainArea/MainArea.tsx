/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useCallback, useState } from "react"
import {
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  Controls,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import { PatternType } from "@/utils/patternUtils"
import TransportNode from "./Graph/Elements/transportNode"
import CustomEdge from "./Graph/Elements/CustomEdge"
import BranchingEdge from "./Graph/Elements/BranchingEdge"
import CustomNode from "./Graph/Elements/CustomNode"
import ModalContainer from "./ModalContainer"
import OasfRecordModal from "./Graph/Directory/OasfRecordModal"
import {
  getGraphConfig,
  updateTransportLabels,
  GraphConfig,
} from "@/utils/graphConfigs"
import {
  isStreamingPattern,
  supportsTransportUpdates,
} from "@/utils/patternUtils"
import { useViewportAwareFitView } from "@/hooks/useViewportAwareFitView"
import { useModalManager } from "@/hooks/useModalManager"
import type { Node, Edge } from "@xyflow/react"
import {EDGE_LABELS} from "@/utils/const.ts";
import {PUBLISH_SUBSCRIBE_CONFIG, GROUP_COMMUNICATION_CONFIG} from "@/utils/graphConfigs";

type DiscoveryResponseEvent = {
  response: string
  ts: number
  sessionId?: string
  senderLabel?: string
}

const proOptions = { hideAttribution: true }

const nodeTypes = {
  transportNode: TransportNode,
  customNode: CustomNode,
}

const edgeTypes = {
  custom: CustomEdge,
  branching: BranchingEdge,
}

interface AnimationStep {
  ids: string[]
}

interface MainAreaProps {
  pattern: PatternType
  buttonClicked: boolean
  setButtonClicked: (clicked: boolean) => void
  aiReplied: boolean
  setAiReplied: (replied: boolean) => void
  chatHeight?: number
  isExpanded?: boolean
  groupCommResponseReceived?: boolean
  onNodeHighlight?: (highlightFunction: (nodeId: string) => void) => void
  discoveryResponseEvent?: DiscoveryResponseEvent | null
}

const DELAY_DURATION = 500
const HIGHLIGHT = {
  ON: true,
  OFF: false,
} as const

const MainArea: React.FC<MainAreaProps> = ({
                                             pattern,
                                             buttonClicked,
                                             setButtonClicked,
                                             aiReplied,
                                             setAiReplied,
                                             chatHeight = 0,
                                             isExpanded = false,
                                             groupCommResponseReceived = false,
                                             onNodeHighlight,
                                             discoveryResponseEvent,
                                           }) => {
  const fitViewWithViewport = useViewportAwareFitView()
  const isGroupCommConnected =
      pattern !== "group_communication" || groupCommResponseReceived
  const config: GraphConfig = getGraphConfig(pattern, isGroupCommConnected)

  const [nodesDraggable, setNodesDraggable] = useState(true)
  const [nodesConnectable, setNodesConnectable] = useState(true)

  const {
    activeModal,
    activeNodeData,
    modalPosition,
    handleOpenIdentityModal,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    handlePaneClick: modalPaneClick,
  } = useModalManager()

  const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges)
  const animationLock = useRef<boolean>(false)

  const seqRef = useRef(0)
  const lastTsRef = useRef<number | null>(null)

  // OASF Modal state
  const [oasfModalOpen, setOasfModalOpen] = useState(false)
  const [oasfModalData, setOasfModalData] = useState<any>(null)
  const [oasfModalPosition, setOasfModalPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 })

  const handleOpenOasfModal = useCallback(
      (nodeData: any, position: { x: number; y: number }) => {
        setOasfModalData(nodeData)
        setOasfModalPosition(position)
        setOasfModalOpen(true)
      },
      [],
  )

  const addDiscoveryResponseGraph = useCallback(
    (_evt: DiscoveryResponseEvent) => {
      console.log("Adding discovery response graph for event:", _evt)

      const responseText = (_evt.response ?? "").toLowerCase()
      // const responseText = "accountant" // for testing

      const hasKeyword = (kw: string) => new RegExp(`\\b${kw}\\b`, "i").test(responseText)

      const kindsToAdd = ([
        "brazil",
        "vietnam",
        "colombia",
        "shipper",
        "accountant",
        "tatooine",
      ] as const).filter(hasKeyword)

      if (kindsToAdd.length === 0) return

      const baseId = ++seqRef.current

      const recruiterNodeId = "recruiter-agent"
      const recruiterPos = { x: 400, y: 300 }

      const templatesByKind: Record<(typeof kindsToAdd)[number], Node | undefined> = {
        brazil: PUBLISH_SUBSCRIBE_CONFIG.nodes.find((n) =>
          String(n.data?.label1 ?? "").toLowerCase().includes("brazil"),
        ),
        vietnam: PUBLISH_SUBSCRIBE_CONFIG.nodes.find((n) =>
          String(n.data?.label1 ?? "").toLowerCase().includes("vietnam"),
        ),
        colombia: PUBLISH_SUBSCRIBE_CONFIG.nodes.find((n) =>
          String(n.data?.label1 ?? "").toLowerCase().includes("colombia"),
        ),
        shipper: GROUP_COMMUNICATION_CONFIG.nodes.find((n) =>
          String(n.data?.label1 ?? "").toLowerCase().includes("shipper"),
        ),
        accountant: GROUP_COMMUNICATION_CONFIG.nodes.find((n) =>
          String(n.data?.label1 ?? "").toLowerCase().includes("accountant"),
        ),
        tatooine: GROUP_COMMUNICATION_CONFIG.nodes.find((n) =>
          String(n.data?.label1 ?? "").toLowerCase().includes("tatooine"),
        ),
      }

      const NODE_WIDTH = 193
      const START_Y_OFFSET = 450
      const HORIZONTAL_GAP = 40

      const makeNodeId = (kind: string) => `discovery-${kind}-${baseId}`

      const cloneTemplateNode = (
        template: Node,
        id: string,
        position: { x: number; y: number },
        parentExists: boolean,
      ): Node => {
        const t: any = template
        const {
          parentId: _parentId,
          extent: _extent,
          expandParent: _expandParent,
          ...rest
        } = t

        return {
          ...rest,
          id,
          position,
          ...(parentExists ? { parentId: t.parentId, extent: t.extent } : {}),
          data: {
            ...(template.data ?? {}),
            active: false,
            isModalOpen: false,
            onOpenIdentityModal: handleOpenIdentityModal,
            onOpenOasfModal: handleOpenOasfModal,
          },
        } as Node
      }

      setNodes((prevNodes) => {
        const existingIds = new Set(prevNodes.map((n) => n.id))

        const total = kindsToAdd.length
        const startCol = -Math.floor(total / 2)

        const newNodes: Node[] = []

        kindsToAdd.forEach((kind, idx) => {
          const template = templatesByKind[kind]
          if (!template) return

          const id = makeNodeId(kind)
          if (existingIds.has(id)) return

          const parentIdNeeded = (template as any)?.parentId as string | undefined
          const parentExists = parentIdNeeded ? existingIds.has(parentIdNeeded) : false

          const colIndex = startCol + idx
          newNodes.push(
            cloneTemplateNode(
              template,
              id,
              {
                x: recruiterPos.x + colIndex * (NODE_WIDTH + HORIZONTAL_GAP),
                y: recruiterPos.y + START_Y_OFFSET,
              },
              parentExists,
            ),
          )
        })

        return newNodes.length ? [...prevNodes, ...newNodes] : prevNodes
      })

      setEdges((prevEdges) => {
        const existingEdgeIds = new Set(prevEdges.map((e) => e.id))

        const newEdges: Edge[] = kindsToAdd
          .map((kind) => {
            const template = templatesByKind[kind]
            if (!template) return null

            const targetId = makeNodeId(kind)
            const edgeId = `edge-${recruiterNodeId}-${baseId}-${targetId}`
            if (existingEdgeIds.has(edgeId)) return null

            // Only connect recruiter -> newly added node
            return {
              id: edgeId,
              source: recruiterNodeId,
              target: targetId,
              data: { label: EDGE_LABELS.A2A_OVER_HTTP },
              type: "custom",
            } as Edge
          })
          .filter(Boolean) as Edge[]

        return newEdges.length ? [...prevEdges, ...newEdges] : prevEdges
      })
    },
    [setNodes, setEdges, handleOpenIdentityModal, handleOpenOasfModal],
  )

  useEffect(() => {
    if (pattern !== "on_demand_discovery") return
    if (!discoveryResponseEvent) return
    if (lastTsRef.current === discoveryResponseEvent.ts) return
    lastTsRef.current = discoveryResponseEvent.ts

    const text = discoveryResponseEvent.response?.trim()
    if (!text) return

    addDiscoveryResponseGraph(discoveryResponseEvent)
  }, [pattern, discoveryResponseEvent, addDiscoveryResponseGraph])

  useEffect(() => {
    animationLock.current = false
  }, [pattern])

  useEffect(() => {
    handleCloseModals()
    setOasfModalOpen(false)
  }, [pattern, handleCloseModals])

  useEffect(() => {
    setNodes((nodes) =>
        nodes.map((node) => ({
          ...node,
          data: { ...node.data, active: false },
        })),
    )
    setEdges([])
  }, [pattern, setNodes, setEdges])

  useEffect(() => {
    const updateGraph = async () => {
      const newConfig = getGraphConfig(pattern, isGroupCommConnected)
      const nodesWithHandlers = newConfig.nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          onOpenIdentityModal: handleOpenIdentityModal,
          onOpenOasfModal: handleOpenOasfModal,
          isModalOpen: !!(activeModal && activeNodeData?.id === node.id),
        },
      }))
      setNodes(nodesWithHandlers)
      await new Promise((resolve) => setTimeout(resolve, 100))
      setEdges(newConfig.edges)
      await updateTransportLabels(
          setNodes,
          setEdges,
          pattern,
          isStreamingPattern(pattern),
      )
      setTimeout(() => {
        fitViewWithViewport({
          chatHeight: 0,
          isExpanded: false,
        })
      }, 200)
    }
    updateGraph()
  }, [
    fitViewWithViewport,
    pattern,
    isGroupCommConnected,
    setNodes,
    setEdges,
    handleOpenIdentityModal,
  ])

  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (!document.hidden && supportsTransportUpdates(pattern)) {
        await updateTransportLabels(
            setNodes,
            setEdges,
            pattern,
            isStreamingPattern(pattern),
        )
      }
    }
    document.addEventListener("visibilitychange", handleVisibilityChange)
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange)
    }
  }, [pattern, setNodes, setEdges])

  useEffect(() => {
    fitViewWithViewport({
      chatHeight,
      isExpanded,
    })
  }, [chatHeight, isExpanded, fitViewWithViewport])

  useEffect(() => {
    const checkEdges = () => {
      const expectedEdges = config.edges.length
      const renderedEdges =
          document.querySelectorAll(".react-flow__edge").length
      if (expectedEdges > 0 && renderedEdges === 0 && !animationLock.current) {
        setEdges([])
        setTimeout(() => {
          setEdges(config.edges)
        }, 100)
      }
    }
    const intervalId = setInterval(checkEdges, 2000)
    const timeoutId = setTimeout(checkEdges, 1000)
    return () => {
      clearInterval(intervalId)
      clearTimeout(timeoutId)
    }
  }, [config.edges, setEdges])

  useEffect(() => {
    const addTooltips = () => {
      const controlButtons = document.querySelectorAll(
          ".react-flow__controls-button",
      )
      const tooltips = ["Zoom In", "Zoom Out", "Fit View", "Lock"]
      controlButtons.forEach((button, index) => {
        if (index < tooltips.length) {
          if (index === 3) {
            const isLocked = !nodesDraggable || !nodesConnectable
            button.setAttribute("data-tooltip", isLocked ? "Unlock" : "Lock")
          } else {
            button.setAttribute("data-tooltip", tooltips[index])
          }
          button.removeAttribute("title")
        }
      })
    }
    const timeoutId = setTimeout(addTooltips, 100)
    return () => clearTimeout(timeoutId)
  }, [pattern, nodesDraggable, nodesConnectable])

  const delay = (ms: number): Promise<void> =>
      new Promise((resolve) => setTimeout(resolve, ms))

  const updateStyle = useCallback(
      (id: string, active: boolean): void => {
        setNodes((nodes) =>
            nodes.map((node) =>
                node.id === id ? { ...node, data: { ...node.data, active } } : node,
            ),
        )
        setTimeout(() => {
          setEdges((edges) =>
              edges.map((edge) =>
                  edge.id === id ? { ...edge, data: { ...edge.data, active } } : edge,
              ),
          )
        }, 10)
      },
      [setNodes, setEdges],
  )

  useEffect(() => {
    const shouldAnimate = buttonClicked && !aiReplied
    if (!shouldAnimate) return
    if (pattern === "group_communication") return
    const waitForAnimationAndRun = async () => {
      while (animationLock.current) {
        await delay(100)
      }
      animationLock.current = true
      const animate = async (ids: string[], active: boolean): Promise<void> => {
        ids.forEach((id: string) => updateStyle(id, active))
        await delay(DELAY_DURATION)
      }
      const animateGraph = async (): Promise<void> => {
        const animationSequence: AnimationStep[] = config.animationSequence
        for (const step of animationSequence) {
          await animate(step.ids, HIGHLIGHT.ON)
          await animate(step.ids, HIGHLIGHT.OFF)
        }
        setButtonClicked(false)
        animationLock.current = false
      }
      await animateGraph()
    }
    waitForAnimationAndRun()
  }, [
    buttonClicked,
    setButtonClicked,
    aiReplied,
    setAiReplied,
    pattern,
    updateStyle,
    setNodes,
    setEdges,
  ])

  const highlightNode = useCallback(
      (nodeId: string) => {
        if (!nodeId) return
        if (pattern === "group_communication") {
          updateStyle(nodeId, HIGHLIGHT.ON)
          setTimeout(() => {
            updateStyle(nodeId, HIGHLIGHT.OFF)
          }, 1800)
        }
      },
      [updateStyle, pattern],
  )

  useEffect(() => {
    if (onNodeHighlight) {
      onNodeHighlight(highlightNode)
    }
  }, [onNodeHighlight, highlightNode])

  const onNodeDrag = useCallback(() => {}, [])
  const onPaneClick = modalPaneClick

  return (
      <div className="bg-primary-bg order-1 flex h-full w-full flex-none flex-grow flex-col items-start self-stretch p-0">
        <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeDrag={onNodeDrag}
            onPaneClick={onPaneClick}
            proOptions={proOptions}
            defaultViewport={{ x: 0, y: 0, zoom: 0.75 }}
            minZoom={0.15}
            maxZoom={1.8}
            nodesDraggable={nodesDraggable}
            nodesConnectable={nodesConnectable}
            elementsSelectable={nodesDraggable}
        >
          <Controls
              onInteractiveChange={(interactiveEnabled) => {
                setNodesDraggable(interactiveEnabled)
                setNodesConnectable(interactiveEnabled)
              }}
          />
        </ReactFlow>

        <ModalContainer
            activeModal={activeModal}
            activeNodeData={activeNodeData}
            modalPosition={modalPosition}
            onClose={handleCloseModals}
            onShowBadgeDetails={handleShowBadgeDetails}
            onShowPolicyDetails={handleShowPolicyDetails}
        />

        <OasfRecordModal
            isOpen={oasfModalOpen}
            onClose={() => setOasfModalOpen(false)}
            nodeName={oasfModalData?.label1 || ""}
            nodeData={oasfModalData}
            position={oasfModalPosition}
        />
      </div>
  )
}

const MainAreaWithProvider: React.FC<MainAreaProps> = (props) => (
    <ReactFlowProvider>
      <MainArea {...props} />
    </ReactFlowProvider>
)

export default MainAreaWithProvider