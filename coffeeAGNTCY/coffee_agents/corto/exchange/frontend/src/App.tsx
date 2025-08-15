/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState, useEffect } from 'react';
import { v4 as uuid } from 'uuid';
import { LOCAL_STORAGE_KEY } from '@/components/Chat/Messages';
import UserMessage from '@/components/Chat/UserMessage';
import AgentIcon from '@/assets/Agent_Icon.svg';

import ChatArea from '@/components/Chat/ChatArea';
import CodePopUp from "@/components/MainArea/CodePopUp";

import Navigation from '@/components/Navigation/Navigation';
import MainArea from '@/components/MainArea/MainArea';

import { Message } from '@/types/Message';
import { useAgentAPI } from '@/hooks/useAgentAPI';

const App: React.FC = () => {
    const [aiReplied, setAiReplied] = useState<boolean>(false);
    const [buttonClicked, setButtonClicked] = useState<boolean>(false);
    const [showCode, setShowCode] = useState<boolean>(false);
    const [currentUserMessage, setCurrentUserMessage] = useState<string>('');
    const [agentResponse, setAgentResponse] = useState<string>('');
    const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false);
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Hi! How can I assist you?', id: uuid(), animate: false }
    ]);

    const { sendMessage } = useAgentAPI();

    useEffect(() => {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages));
    }, [messages]);

    const handleApiResponse = (response: string, isError: boolean = false) => {
        setAgentResponse(response);
        setIsAgentLoading(false);
        
        setMessages(prev => {
            const updated = [...prev];
            if (updated.length > 0 && updated[updated.length - 1].role === 'assistant') {
                updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    content: response,
                    animate: !isError
                };
            }
            return updated;
        });
    };

    const handleDropdownSelect = async (query: string) => {
        setCurrentUserMessage(query);
        setIsAgentLoading(true);
        
        try {
            const response = await sendMessage(query);
            handleApiResponse(response, false);
        } catch (error) {
            // Log error properly instead of using console.error
            if (process.env.NODE_ENV === 'development') {
                console.warn('API Error:', error);
            }
            handleApiResponse('Sorry, I encountered an error.', true);
        }
    };

    return (
        <div className="flex flex-col w-screen h-screen overflow-hidden bg-primary-bg">
            <Navigation />

            <div className="flex-grow flex flex-col bg-primary-bg">
            

                <div className="flex-grow flex flex-col bg-primary-bg">
                    <div className="relative">
                        <CodePopUp 
                            showCode={showCode}
                            onClose={() => setShowCode(false)}
                        />
                    </div>
                    <div className="flex-grow relative">
                        <MainArea 
                            buttonClicked={buttonClicked}
                            setButtonClicked={setButtonClicked}
                            aiReplied={aiReplied}
                            setAiReplied={setAiReplied}
                        />
                    </div>
                </div>
            </div>

            <div className="flex flex-col justify-center items-center p-0 gap-0 w-full min-h-[76px] bg-[#2E3E57] flex-none self-stretch flex-grow-0 min-w-[1440px] box-border overflow-visible">
                {currentUserMessage && (
                    <div className="w-full p-4">
                        <div className="w-[830px] max-w-full mx-auto flex flex-col gap-3">
                            <UserMessage content={currentUserMessage} />
                            {(isAgentLoading || agentResponse) && (
                                <div className="flex flex-row items-start gap-1 w-full">
                                    <div className="flex justify-center items-center w-10 h-10 bg-[#2E3E57] rounded-full">
                                        <img src={AgentIcon} alt="Agent" className="w-10 h-10 rounded-full" style={{opacity: 1}} />
                                    </div>
                                    <div className="flex flex-col justify-center items-start p-1 px-2 w-[764px] rounded">
                                        <div className="font-inter font-normal text-sm leading-5 text-white whitespace-pre-wrap">
                                            {isAgentLoading ? (
                                                <div className="text-[#649EF5] animate-pulse">...</div>
                                            ) : (
                                                agentResponse
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
                
                <ChatArea
                    messages={messages}
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                    setAiReplied={setAiReplied}
                    isBottomLayout={true}
                    showCoffeeDropdown={true}
                    onDropdownSelect={handleDropdownSelect}
                    onApiResponse={handleApiResponse}
                />
            </div>
        </div>
    );
};

export default App;