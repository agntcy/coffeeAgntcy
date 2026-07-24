/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Default root page at / — main app (sidebar + chat + graph).
 **/

import React, { useMemo, useRef } from "react"
import {
  Group,
  Panel,
  useDefaultLayout,
  usePanelRef,
} from "react-resizable-panels"
import { Box } from "@open-ui-kit/core"
import { skipLinkSx } from "@/utils/a11ySx"
import Navigation from "@/components/Navigation/Navigation"
import CanvasSwitch from "@/components/MainArea/CanvasSwitch"
import ChatArea from "@/components/Chat/ChatArea"
import ChatPanelSeparator from "@/components/Chat/ChatPanelSeparator"
import {
  CHAT_MAX_SIZE,
  CHAT_MIN_SIZE,
  CHAT_PANEL_ID,
  GRAPH_MIN_SIZE,
  GRAPH_PANEL_ID,
  MAIN_VERTICAL_GROUP_ID,
} from "@/components/Chat/chatPanelLayout"
import { useChatPanelContentSize } from "@/hooks/useChatPanelContentSize"
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
import { CanvasMode } from "@/types/patternDoc"
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
    suggestedPromptsUrl,
    chatHeightValue,
    isExpanded,
    chatRef,
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
    handleUserInput,
    handleApiResponse,
    handleSendPrompt,
    handleStreamComplete,
    handleClearConversation,
    handleNodeHighlightSetup,
    handleSenderHighlight,
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
    selectedReferencePattern,
    selectReferencePattern,
    canvasMode,
    patternDocState,
    patternChatSessionId,
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

  const hasChatMessages = Boolean(currentUserMessage?.trim())
  const chatPanelRef = usePanelRef()
  const { fillHeight: chatPanelFillHeight } = useChatPanelContentSize({
    enabled: hasChatMessages,
    chatPanelRef,
    chatContentRef: chatRef,
  })

  const {
    defaultLayout: mainVerticalDefaultLayout,
    onLayoutChanged: onMainVerticalLayoutChanged,
  } = useDefaultLayout({
    id: MAIN_VERTICAL_GROUP_ID,
    panelIds: hasChatMessages
      ? [GRAPH_PANEL_ID, CHAT_PANEL_ID]
      : [GRAPH_PANEL_ID],
  })

  const chatAreaProps = {
    isBottomLayout: true as const,
    canvasMode,
    selectedReferencePattern,
    patternChatSessionId,
    onPatternChatSuccess: () => setAiReplied(true),
    suggestedPromptsUrl,
    showProgressTracker:
      canvasMode !== CanvasMode.PATTERN_DOC && showProgressTracker,
    showAuctionStreaming:
      canvasMode !== CanvasMode.PATTERN_DOC && showAuctionStreaming,
    showRecruiterStreaming:
      canvasMode !== CanvasMode.PATTERN_DOC && showRecruiterStreaming,
    showFinalResponse,
    onStreamComplete: handleStreamComplete,
    onSenderHighlight: handleSenderHighlight,
    graphConfig,
    onSendPrompt: handleSendPrompt,
    onUserInput: handleUserInput,
    onApiResponse: handleApiResponse,
    onClearConversation: handleClearConversation,
    currentUserMessage,
    agentResponse,
    executionKey,
    isAgentLoading,
    apiError,
    chatRef,
    fillHeight: hasChatMessages ? chatPanelFillHeight : false,
    auctionState: {
      events,
      status,
      error,
    },
    recruiterState: {
      events: recruiterEvents,
      status: recruiterStatus,
      error: recruiterError,
      sessionId: recruiterSessionId,
      finalMessage: recruiterFinalMessage,
      agentRecords: recruiterAgentRecords,
      evaluationResults: recruiterEvaluationResults,
      selectedAgent: recruiterSelectedAgent,
    },
  }

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
              selectedReferencePattern={selectedReferencePattern}
              onSelectReferencePattern={selectReferencePattern}
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
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    width: "100%",
                    height: "100%",
                    minHeight: 0,
                    overflow: "hidden",
                  }}
                >
                  <Group
                    id={MAIN_VERTICAL_GROUP_ID}
                    orientation="vertical"
                    defaultLayout={mainVerticalDefaultLayout}
                    onLayoutChanged={onMainVerticalLayoutChanged}
                    style={{ flex: 1, minHeight: 0, width: "100%" }}
                  >
                    <Panel
                      id={GRAPH_PANEL_ID}
                      minSize={hasChatMessages ? GRAPH_MIN_SIZE : undefined}
                      defaultSize={hasChatMessages ? undefined : "100%"}
                    >
                      <Box
                        component="section"
                        aria-label="Workflow graph"
                        ref={graphSectionRef}
                        sx={{
                          position: "relative",
                          width: "100%",
                          height: "100%",
                          minWidth: 0,
                          minHeight: 0,
                          overflow: "hidden",
                        }}
                      >
                        <CanvasSwitch
                          canvasMode={canvasMode}
                          selectedReferencePattern={selectedReferencePattern}
                          patternDocState={patternDocState}
                          pattern={selectedPattern}
                          selectedWorkflowSummary={selectedWorkflowSummary}
                          workflowCatalogLoading={workflowCatalogLoading}
                          workflowCatalogError={workflowCatalogError}
                          onLiveGraphConfig={setLiveGraphConfig}
                          buttonClicked={buttonClicked}
                          setButtonClicked={setButtonClicked}
                          aiReplied={aiReplied}
                          chatHeight={chatHeightValue}
                          isExpanded={isExpanded}
                          groupCommResponseReceived={groupCommResponseReceived}
                          onNodeHighlight={handleNodeHighlightSetup}
                          selectedAgentCid={
                            typeof recruiterSelectedAgent?.cid === "string"
                              ? recruiterSelectedAgent.cid
                              : null
                          }
                        />
                      </Box>
                    </Panel>
                    {hasChatMessages ? (
                      <>
                        <ChatPanelSeparator />
                        <Panel
                          id={CHAT_PANEL_ID}
                          panelRef={chatPanelRef}
                          minSize={CHAT_MIN_SIZE}
                          maxSize={CHAT_MAX_SIZE}
                        >
                          <Box
                            component="section"
                            aria-label="Agent chat"
                            sx={{
                              display: "flex",
                              width: "100%",
                              height: chatPanelFillHeight ? "100%" : "auto",
                              minWidth: 0,
                              minHeight: 0,
                              flexDirection: "column",
                              overflow: "hidden",
                            }}
                          >
                            <ChatArea {...chatAreaProps} />
                          </Box>
                        </Panel>
                      </>
                    ) : null}
                  </Group>
                  {!hasChatMessages ? (
                    <Box
                      component="section"
                      aria-label="Agent chat"
                      sx={{
                        display: "flex",
                        width: "100%",
                        flexShrink: 0,
                        flexDirection: "column",
                        overflow: "hidden",
                      }}
                    >
                      <ChatArea {...chatAreaProps} />
                    </Box>
                  ) : null}
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
