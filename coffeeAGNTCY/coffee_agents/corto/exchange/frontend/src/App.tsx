/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState, useEffect } from 'react';
import { v4 as uuid } from 'uuid';
import { LOCAL_STORAGE_KEY } from '@/components/Chat/Messages';

import ChatArea from '@/components/Chat/ChatArea';
import CodePopUp from "@/components/MainArea/CodePopUp";

import Navigation from '@/components/Navigation/Navigation';
import MainArea from '@/components/MainArea/MainArea';
import Sidebar from '@/components/Sidebar/Sidebar';

import { Message } from '@/types/Message';
import { useAgentAPI } from '@/hooks/useAgentAPI';

const App: React.FC = () => {
    const [aiReplied, setAiReplied] = useState<boolean>(false);
    const [buttonClicked, setButtonClicked] = useState<boolean>(false);
    const [showCode, setShowCode] = useState<boolean>(false);
    const [currentUserMessage, setCurrentUserMessage] = useState<string>('');
    const [agentResponse, setAgentResponse] = useState<string>('');
    const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false);
    const [selectedView, setSelectedView] = useState<'coffee-grading' | 'agent-to-agent'>('agent-to-agent');
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
            updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: response,
                animate: !isError
            };
            return updated;
        });
    };

    const handleUserInput = (query: string) => {
        setCurrentUserMessage(query);
        setIsAgentLoading(true);
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

    const handleViewChange = (view: 'coffee-grading' | 'agent-to-agent') => {
        setSelectedView(view);
    };

    return (
        <div className="flex flex-col w-screen h-screen overflow-hidden bg-primary-bg">
            <Navigation />

            <div className="flex flex-1 overflow-hidden">
           
                <Sidebar 
                    selectedView={selectedView}
                    onViewChange={handleViewChange}
                />
                
                <div 
                    className="flex-1 flex flex-col border-l border-[#00142B] bg-primary-bg"
                >
                    <div className="relative">
                        <CodePopUp 
                            showCode={showCode}
                            onClose={() => setShowCode(false)}
                        />
                    </div>
                    {selectedView === 'agent-to-agent' && (
                        <div className="flex-grow relative">
                            <MainArea 
                                buttonClicked={buttonClicked}
                                setButtonClicked={setButtonClicked}
                                aiReplied={aiReplied}
                                setAiReplied={setAiReplied}
                            />
                        </div>
                    )}
                    {selectedView === 'coffee-grading' && (
                        <div className="flex-grow flex items-center justify-center">
                            <div className="text-white text-xl">Coffee Grading Conversation View</div>
                        </div>
                    )}

                    <div className="flex flex-col justify-center items-center p-0 gap-0 w-full min-h-[76px] bg-[#2E3E57] flex-none">
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
                            currentUserMessage={currentUserMessage}
                            agentResponse={agentResponse}
                            isAgentLoading={isAgentLoading}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default App;