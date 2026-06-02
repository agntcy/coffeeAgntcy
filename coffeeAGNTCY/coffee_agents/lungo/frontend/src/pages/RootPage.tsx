/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Default root page at / — main app (sidebar + chat + graph).
 **/

import React from "react"
import { Box } from "@open-ui-kit/core"
import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import ChatArea from "@/components/Chat/ChatArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import { PATTERNS } from "@/utils/patternUtils"
import { useApp } from "@/useApp"

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

  return (
    <Box
      sx={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Navigation />
      <Box
        sx={{
          display: "flex",
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        <Sidebar
          selectedWorkflowSummary={selectedWorkflowSummary}
          summaries={workflowCatalogSummaries}
          isLoading={workflowCatalogLoading}
          error={workflowCatalogError}
          onSelectWorkflow={selectWorkflowFromCatalog}
        />
        <Box
          sx={{
            display: "flex",
            flex: 1,
            minWidth: 0,
            minHeight: 0,
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <Box
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
              minHeight: { xs: "min(76px, 50%)", md: "min(96px, 50%)" },
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
        </Box>
      </Box>
    </Box>
  )
}

export default RootPage
