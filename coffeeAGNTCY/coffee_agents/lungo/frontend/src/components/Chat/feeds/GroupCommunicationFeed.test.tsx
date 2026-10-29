/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { render, screen } from "@testing-library/react"
import type { Node } from "@xyflow/react"
import { useState } from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { useGroupStreamingStore } from "@/stores/groupStreamingStore"
import { NDJSON_STREAMING_STATUS } from "@/stores/ndjsonStreamingStatus"
import type { GraphConfig } from "@/utils/graphConfigs"
import GroupCommunicationFeed from "./GroupCommunicationFeed"

const node = (id: string, label: string): Node => ({
  id,
  type: "customNode",
  position: { x: 0, y: 0 },
  data: { label },
})

const graphConfig: GraphConfig = {
  title: "Supply Chain Commitment",
  animationSequence: [],
  nodes: [
    node("buyer-node", "Buyer"),
    node("supplier-a-node", "Supplier A"),
    node("supplier-b-node", "Supplier B"),
  ],
  edges: [],
}

const renderFeed = (onSenderHighlight = vi.fn()) => {
  render(
    <ThemeProvider>
      <GroupCommunicationFeed
        isVisible
        prompt="I'd like to have a 1,000-tonne coffee shipment"
        apiError={false}
        graphConfig={graphConfig}
        onSenderHighlight={onSenderHighlight}
      />
    </ThemeProvider>,
  )
  return onSenderHighlight
}

describe("GroupCommunicationFeed with supply chain events", () => {
  beforeEach(() => {
    useGroupStreamingStore.getState().reset()
  })

  it("renders negotiation events and highlights the sender node", () => {
    const { addNegotiationEvent } = useGroupStreamingStore.getState()
    useGroupStreamingStore.setState({
      status: NDJSON_STREAMING_STATUS.STREAMING,
    })
    addNegotiationEvent({
      type: "message",
      seq: 2,
      from: "supplier_b",
      to: ["buyer"],
      kind: "negotiation",
      phase: "round_1",
      plan_version: 0,
      reply_to: 1,
      body: "Supplier B can offer 350 tonnes.",
    })

    const onSenderHighlight = renderFeed()

    expect(screen.getByTestId("supply-chain-message")).toHaveTextContent(
      "Supplier B can offer 350 tonnes.",
    )
    expect(onSenderHighlight).toHaveBeenCalledWith("supplier-b-node")
  })

  it("highlights the Buyer node for a moderator message", () => {
    const { addNegotiationEvent } = useGroupStreamingStore.getState()
    useGroupStreamingStore.setState({
      status: NDJSON_STREAMING_STATUS.STREAMING,
    })
    addNegotiationEvent({
      type: "message",
      seq: 9,
      from: "moderator",
      to: ["supplier_c"],
      kind: "event",
      phase: null,
      plan_version: 1,
      reply_to: null,
      body: "Your ready time changed.",
    })

    const onSenderHighlight = renderFeed()

    expect(onSenderHighlight).toHaveBeenCalledWith("buyer-node")
  })

  it("does not loop when the parent re-renders on every highlight", () => {
    const { addNegotiationEvent } = useGroupStreamingStore.getState()
    useGroupStreamingStore.setState({
      status: NDJSON_STREAMING_STATUS.STREAMING,
    })
    addNegotiationEvent({
      type: "message",
      seq: 2,
      from: "supplier_a",
      to: ["buyer"],
      kind: "negotiation",
      phase: "round_1",
      plan_version: 0,
      reply_to: 1,
      body: "Supplier A can offer 400 tonnes.",
    })
    const highlighted = vi.fn()

    // Like the real parent: highlighting sets state, and both the callback
    // and the graph config are new objects on every render.
    const Parent = () => {
      const [, setNodeId] = useState<string | null>(null)
      return (
        <GroupCommunicationFeed
          isVisible
          prompt="p"
          apiError={false}
          graphConfig={{ ...graphConfig }}
          onSenderHighlight={(id: string) => {
            highlighted(id)
            setNodeId(id)
          }}
        />
      )
    }
    render(
      <ThemeProvider>
        <Parent />
      </ThemeProvider>,
    )

    expect(highlighted).toHaveBeenCalledTimes(1)
    expect(highlighted).toHaveBeenCalledWith("supplier-a-node")
  })

  it("shows the verdict card once the run is complete", () => {
    const { addNegotiationEvent } = useGroupStreamingStore.getState()
    addNegotiationEvent({
      type: "verdict",
      verdict: {
        verdict: "FAIL",
        codes: ["LATE_LOT"],
        details: [],
        lots: [],
        silent: true,
      },
    })
    useGroupStreamingStore.setState({
      status: NDJSON_STREAMING_STATUS.COMPLETED,
    })

    renderFeed()

    expect(screen.getByTestId("supply-chain-silent-badge")).toBeInTheDocument()
    expect(screen.getByText("Collapse details")).toBeInTheDocument()
  })
})
