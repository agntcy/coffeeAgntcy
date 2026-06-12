/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Default root page at / — main app (sidebar + chat + graph).
 **/

import React, { useMemo, useRef } from "react"
import { Group, Panel, useDefaultLayout } from "react-resizable-panels"
import { Box } from "@open-ui-kit/core"
import { skipLinkSx } from "@/utils/a11ySx"
import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import ChatArea from "@/components/Chat/ChatArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import SidebarPanelSeparator from "@/components/Sidebar/SidebarPanelSeparator"
import {
  APP_SHELL_PANEL_GROUP_ID,
  MAIN_MIN_SIZE,
  MAIN_PANEL_ID,
  SIDEBAR_DEFAULT_SIZE,
  SIDEBAR_MAX_SIZE,
  SIDEBAR_MIN_SIZE,
  SIDEBAR_PANEL_ID,
} from "@/components/Sidebar/sidebarPanelLayout"
import { PATTERNS } from "@/utils/patternUtils"
import { useApp } from "@/useApp"
import { GraphCanvasLayoutContext } from "@/contexts/graphCanvasLayout"
import { useElementWidth } from "@/hooks/useElementWidth"
import { useElementRect } from "@/hooks/useElementRect"

const RootPage: React.FC = () => {
  const {
    selectedPattern,
    selectWorkflowFromCatalog,
    workflowCatalogSummaries,
    workflowCatalogLoading,
    workflowCatalogError,
    selectedWorkflowSummary,
    chatHeightValue,
    isExpanded,
    chatRef,
    setMessages,
    aiReplied,
    setAiReplied,
    buttonClicked,
    setButtonClicked,
    currentUserMessage,
    agentResponse,
    executionKey,
    isAgentLoading,
    apiError,
    showProgressTracker,
    showAuctionStreaming,
    showRecruiterStreaming,
    showFinalResponse,
    groupCommResponseReceived,
    discoveryResponseEvent,
    handleUserInput,
    handleApiResponse,
    handleDropdownSelect,
    handleStreamComplete,
    handleClearConversation,
    handleNodeHighlightSetup,
    handleSenderHighlight,
    handleDiscoveryResponse,
    graphConfig,
    events,
    status,
    error,
    recruiterEvents,
    recruiterStatus,
    recruiterError,
    recruiterSessionId,
    recruiterFinalMessage,
    recruiterAgentRecords,
    recruiterEvaluationResults,
    recruiterSelectedAgent,
    setLiveGraphConfig,
  } = useApp()

  const graphSectionRef = useRef<HTMLElement>(null)
  const mainContentRef = useRef<HTMLElement>(null)
  const graphCanvasWidth = useElementWidth(graphSectionRef)
  const mainContentRect = useElementRect(mainContentRef)

  const graphCanvasLayout = useMemo(
    () => ({
      graphCanvasWidth,
      mainContentLeft: mainContentRect?.left,
      mainContentWidth: mainContentRect?.width,
    }),
    [graphCanvasWidth, mainContentRect?.left, mainContentRect?.width],
  )

  const { defaultLayout, onLayoutChanged } = useDefaultLayout({
    id: APP_SHELL_PANEL_GROUP_ID,
    panelIds: [SIDEBAR_PANEL_ID, MAIN_PANEL_ID],
  })

  return (
    <Box
      sx={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        flexDirection: "column",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <Box component="a" href="#main-content" sx={skipLinkSx}>
        Skip to main content
      </Box>
      <Navigation />
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          minWidth: 0,
          overflow: "hidden",
        }}
      >
        <Group
          id={APP_SHELL_PANEL_GROUP_ID}
          orientation="horizontal"
          defaultLayout={defaultLayout}
          onLayoutChanged={onLayoutChanged}
          style={{ height: "100%", width: "100%" }}
        >
          <Panel
            id={SIDEBAR_PANEL_ID}
            defaultSize={SIDEBAR_DEFAULT_SIZE}
            minSize={SIDEBAR_MIN_SIZE}
            maxSize={SIDEBAR_MAX_SIZE}
          >
            <Sidebar
              selectedWorkflowSummary={selectedWorkflowSummary}
              summaries={workflowCatalogSummaries}
              isLoading={workflowCatalogLoading}
              error={workflowCatalogError}
              onSelectWorkflow={selectWorkflowFromCatalog}
            />
          </Panel>
          <SidebarPanelSeparator />
          <Panel id={MAIN_PANEL_ID} minSize={MAIN_MIN_SIZE}>
            <Box
              component="main"
              id="main-content"
              ref={mainContentRef}
              aria-label="Workflow graph and agent chat"
              sx={{
                display: "flex",
                width: "100%",
                height: "100%",
                minWidth: 0,
                minHeight: 0,
                flexDirection: "column",
                overflow: "hidden",
              }}
            >
              <GraphCanvasLayoutContext.Provider value={graphCanvasLayout}>
                <Box
                  component="section"
                  aria-label="Workflow graph"
                  ref={graphSectionRef}
                  sx={{
                    position: "relative",
                    flex: "1 1 50%",
                    minHeight: "50%",
                    minWidth: 0,
                    overflow: "hidden",
                  }}
                >
                  <MainArea
                    pattern={selectedPattern}
                    selectedWorkflowSummary={selectedWorkflowSummary}
                    onLiveGraphConfig={setLiveGraphConfig}
                    buttonClicked={buttonClicked}
                    setButtonClicked={setButtonClicked}
                    aiReplied={aiReplied}
                    setAiReplied={setAiReplied}
                    chatHeight={chatHeightValue}
                    isExpanded={isExpanded}
                    groupCommResponseReceived={groupCommResponseReceived}
                    onNodeHighlight={handleNodeHighlightSetup}
                    discoveryResponseEvent={discoveryResponseEvent}
                    selectedAgentCid={
                      typeof recruiterSelectedAgent?.cid === "string"
                        ? recruiterSelectedAgent.cid
                        : null
                    }
                  />
                </Box>
                <Box
                  component="section"
                  aria-label="Agent chat"
                  sx={{
                    display: "flex",
                    width: "100%",
                    flex: "0 1 auto",
                    flexShrink: 0,
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "flex-start",
                    gap: 0,
                    p: 0,
                    maxHeight: "50%",
                    minWidth: 0,
                    overflow: "hidden",
                  }}
                >
                  <ChatArea
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                    setAiReplied={setAiReplied}
                    isBottomLayout={true}
                    showCoffeePrompts={
                      selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE ||
                      selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING
                    }
                    showLogisticsPrompts={
                      selectedPattern === PATTERNS.GROUP_MESSAGING
                    }
                    showDiscoveryPrompts={selectedPattern === PATTERNS.A2A_HTTP}
                    showProgressTracker={showProgressTracker}
                    showAuctionStreaming={showAuctionStreaming}
                    showRecruiterStreaming={showRecruiterStreaming}
                    showFinalResponse={showFinalResponse}
                    onStreamComplete={handleStreamComplete}
                    onSenderHighlight={handleSenderHighlight}
                    pattern={selectedPattern}
                    graphConfig={graphConfig}
                    onDropdownSelect={handleDropdownSelect}
                    onUserInput={handleUserInput}
                    onApiResponse={handleApiResponse}
                    onClearConversation={handleClearConversation}
                    currentUserMessage={currentUserMessage}
                    agentResponse={agentResponse}
                    executionKey={executionKey}
                    isAgentLoading={isAgentLoading}
                    apiError={apiError}
                    chatRef={chatRef}
                    auctionState={{
                      events,
                      status,
                      error,
                    }}
                    recruiterState={{
                      events: recruiterEvents,
                      status: recruiterStatus,
                      error: recruiterError,
                      sessionId: recruiterSessionId,
                      finalMessage: recruiterFinalMessage,
                      agentRecords: recruiterAgentRecords,
                      evaluationResults: recruiterEvaluationResults,
                      selectedAgent: recruiterSelectedAgent,
                    }}
                    onDiscoveryResponse={handleDiscoveryResponse}
                  />
                </Box>
              </GraphCanvasLayoutContext.Provider>
            </Box>
          </Panel>
        </Group>
      </Box>
    </Box>
  )
}

export default RootPage
