/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
import ChatArea from "@/components/Chat/ChatArea"
import Sidebar from "@/components/Sidebar/Sidebar"
import { ThemeProvider } from "@/contexts/ThemeContext"
import { PATTERNS } from "@/utils/patternUtils"
import { useApp } from "./useApp"

const App: React.FC = () => {
  const {
    selectedPattern,
    handlePatternChange,
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
  } = useApp()

  return (
    <ThemeProvider>
      <div className="bg-primary-bg flex h-screen w-screen flex-col overflow-hidden">
        <Navigation />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar
            selectedPattern={selectedPattern}
            onPatternChange={handlePatternChange}
          />
          <div className="flex flex-1 flex-col border-l border-action-background bg-app-background">
            <div className="relative flex-grow">
              <MainArea
                pattern={selectedPattern}
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
            </div>
            <div className="flex min-h-[76px] w-full flex-none flex-col items-center justify-center gap-0 bg-overlay-background p-0 md:min-h-[96px]">
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
                  selectedPattern === PATTERNS.GROUP_COMMUNICATION
                }
                showDiscoveryPrompts={
                  selectedPattern === PATTERNS.ON_DEMAND_DISCOVERY
                }
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
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App
