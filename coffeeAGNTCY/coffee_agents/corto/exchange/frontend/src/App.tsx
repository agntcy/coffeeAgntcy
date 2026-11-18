/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useMemo, useRef } from "react"
import {
  Group,
  Panel,
  useDefaultLayout,
  usePanelRef,
} from "react-resizable-panels"
import { Box } from "@open-ui-kit/core"
import { LOCAL_STORAGE_KEY } from "@/components/Chat/Messages"

import ChatArea from "@/components/Chat/ChatArea"
import {
  CHAT_MAX_SIZE,
  CHAT_MIN_SIZE,
  CHAT_PANEL_ID,
  ChatPanelSeparator,
  GRAPH_MIN_SIZE,
  GRAPH_PANEL_ID,
  MAIN_VERTICAL_GROUP_ID,
} from "@/components/Chat/panel"
import Navigation from "@/components/Navigation/Navigation"
import MainArea from "@/components/MainArea/MainArea"
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
import { GraphCanvasLayoutContext } from "@/contexts/graphCanvasLayout"
import {
  useElementRect,
  useElementWidth,
  useIsBelowSmBreakpoint,
} from "@/hooks/layout"
import { useChatPanelContentSize } from "@/hooks/useChatPanelContentSize"
import { skipLinkSx } from "@/utils/a11ySx"
import { Message } from "./types/Message"
import { useAgentAPI } from "@/hooks/useAgentAPI"
import { logger } from "./utils/logger"
import { parseApiError } from "@/utils/const.ts"

const App: React.FC = () => {
  const [aiReplied, setAiReplied] = useState<boolean>(false)
  const [buttonClicked, setButtonClicked] = useState<boolean>(false)
  const [currentUserMessage, setCurrentUserMessage] = useState<string>("")
  const [agentResponse, setAgentResponse] = useState<string>("")
  const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false)
  const [isChatMinimized, setIsChatMinimized] = useState<boolean>(false)
  const [messages, setMessages] = useState<Message[]>([])
  const { sendMessageWithCallback } = useAgentAPI()

  const isCompactShell = useIsBelowSmBreakpoint()
  const chatRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const storedMessages = localStorage.getItem(LOCAL_STORAGE_KEY)
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages))
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

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

  const appShellPanelIds = useMemo(
    () =>
      isCompactShell ? [MAIN_PANEL_ID] : [SIDEBAR_PANEL_ID, MAIN_PANEL_ID],
    [isCompactShell],
  )

  const { defaultLayout, onLayoutChanged } = useDefaultLayout({
    id: APP_SHELL_PANEL_GROUP_ID,
    panelIds: appShellPanelIds,
  })

  const hasChatMessages = Boolean(currentUserMessage?.trim())
  const chatExpanded = hasChatMessages && !isChatMinimized
  const chatPanelRef = usePanelRef()
  const { fillHeight: chatPanelFillHeight } = useChatPanelContentSize({
    enabled: true,
    remeasureKey: `${hasChatMessages}:${isChatMinimized}`,
    fillPanelHeight: chatExpanded,
    chatPanelRef,
    chatContentRef: chatRef,
  })

  const {
    defaultLayout: mainVerticalDefaultLayout,
    onLayoutChanged: onMainVerticalLayoutChanged,
  } = useDefaultLayout({
    id: MAIN_VERTICAL_GROUP_ID,
    panelIds: [GRAPH_PANEL_ID, CHAT_PANEL_ID],
  })

  const handleApiResponse = (response: string, isError: boolean = false) => {
    setAgentResponse(response)
    setIsAgentLoading(false)

    setMessages((prev) => {
      const updated = [...prev]
      updated[updated.length - 1] = {
        ...updated[updated.length - 1],
        content: response,
        animate: !isError,
      }
      return updated
    })
  }

  const handleUserInput = (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)
  }

  const handleDropdownSelect = async (query: string) => {
    setCurrentUserMessage(query)
    setIsAgentLoading(true)

    try {
      await sendMessageWithCallback(query, setMessages, {
        onStart: () => {
          setButtonClicked(true)
        },

        onSuccess: (response) => {
          setAiReplied(true)
          handleApiResponse(response, false)
        },

        onError: (error) => {
          if (import.meta.env.DEV) {
            logger.apiError("/agent/prompt", error)
          }

          const { status, message } = parseApiError(error)

          if (!message && !status) {
            handleApiResponse(
              "Sorry, I encountered an error. Please try again later.",
              true,
            )
            return
          }

          if (status && status >= 400 && status < 500 && message) {
            handleApiResponse(`HTTP ${status} - ${message}`, true)
            return
          }

          handleApiResponse(message, true)
          return
        },
      })
    } catch (error) {
      if (import.meta.env.DEV) {
        logger.apiError("/agent/prompt", error)
      }

      handleApiResponse(
        "Sorry, I encountered an error. Please try again later.",
        true,
      )
    }
  }

  const handleClearConversation = () => {
    setMessages([])
    setCurrentUserMessage("")
    setAgentResponse("")
    setIsAgentLoading(false)
    setIsChatMinimized(false)
    setButtonClicked(false)
    setAiReplied(false)
  }

  return (
    <Box
      sx={{
        display: "flex",
        height: "100vh",
        width: "100%",
        flexDirection: "column",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <Box component="a" href="#main-content" sx={skipLinkSx}>
        Skip to main content
      </Box>
      <Navigation catalogSidebarProps={isCompactShell ? {} : undefined} />

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
          {!isCompactShell ? (
            <>
              <Panel
                id={SIDEBAR_PANEL_ID}
                defaultSize={SIDEBAR_DEFAULT_SIZE}
                minSize={SIDEBAR_MIN_SIZE}
                maxSize={SIDEBAR_MAX_SIZE}
              >
                <Sidebar />
              </Panel>
              <SidebarPanelSeparator />
            </>
          ) : null}

          <Panel id={MAIN_PANEL_ID} minSize={MAIN_MIN_SIZE} defaultSize="100%">
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
                      minSize={chatExpanded ? GRAPH_MIN_SIZE : undefined}
                      defaultSize={chatExpanded ? undefined : "100%"}
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
                        <MainArea
                          buttonClicked={buttonClicked}
                          setButtonClicked={setButtonClicked}
                          aiReplied={aiReplied}
                          setAiReplied={setAiReplied}
                        />
                      </Box>
                    </Panel>
                    {!isCompactShell ? (
                      <ChatPanelSeparator disabled={!chatExpanded} />
                    ) : null}
                    <Panel
                      id={CHAT_PANEL_ID}
                      panelRef={chatPanelRef}
                      minSize={chatExpanded ? CHAT_MIN_SIZE : undefined}
                      maxSize={CHAT_MAX_SIZE}
                      style={{ overflow: "hidden" }}
                    >
                      <Box
                        component="section"
                        aria-label="Agent chat"
                        sx={{
                          display: "flex",
                          width: "100%",
                          height: chatPanelFillHeight ? "100%" : "fit-content",
                          minWidth: 0,
                          minHeight: chatPanelFillHeight ? 0 : "fit-content",
                          flex: chatExpanded ? undefined : "0 0 auto",
                          alignSelf: chatExpanded ? undefined : "flex-start",
                          flexDirection: "column",
                          overflow: "hidden",
                        }}
                      >
                        <ChatArea
                          messages={messages}
                          setMessages={setMessages}
                          setButtonClicked={setButtonClicked}
                          setAiReplied={setAiReplied}
                          isBottomLayout={true}
                          showCoffeeDropdown={true}
                          onDropdownSelect={handleDropdownSelect}
                          onUserInput={handleUserInput}
                          onApiResponse={handleApiResponse}
                          onClearConversation={handleClearConversation}
                          currentUserMessage={currentUserMessage}
                          agentResponse={agentResponse}
                          isAgentLoading={isAgentLoading}
                          chatRef={chatRef}
                          isMinimized={isChatMinimized}
                          onMinimizedChange={setIsChatMinimized}
                          fillHeight={
                            chatExpanded ? chatPanelFillHeight : false
                          }
                        />
                      </Box>
                    </Panel>
                  </Group>
                </Box>
              </GraphCanvasLayoutContext.Provider>
            </Box>
          </Panel>
        </Group>
      </Box>
    </Box>
  )
}

export default App
