/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState, useEffect } from 'react';
import { v4 as uuid } from 'uuid';
import { LOCAL_STORAGE_KEY } from '@/components/Chat/Messages';
import UserMessage from '@/components/Chat/UserMessage';
import AgentIcon from '@/assets/Agent_Icon.svg';

import BottomChat from '@/components/Chat/ChatArea';

import Navigation from '@/components/Navigation/Navigation';
import PatternEmptyState from '@/components/MainArea/PatternEmptyState';
import MainArea from '@/components/MainArea/MainArea';
import { useAgentAPI } from '@/hooks/useAgentAPI';

export const PATTERNS = {
  NONE: 'none',
  SLIM_A2A: 'slim_a2a',
  SLIM_MULTI_A2A: 'slim_multi_a2a',
  IDENTITY: 'identity'
} as const;

export type PatternType = typeof PATTERNS[keyof typeof PATTERNS];


export interface Message {
    role: 'assistant' | 'user';
    content: string;
    id: string;
    animate: boolean;
}


type PatternMessages = {
    [K in Exclude<PatternType, 'none'>]: string;
};

const App: React.FC = () => {
    const { sendMessage } = useAgentAPI();

    const [selectedPattern, setSelectedPattern] = useState<PatternType>(PATTERNS.NONE);
    const [aiReplied, setAiReplied] = useState<boolean>(false);
    const [buttonClicked, setButtonClicked] = useState<boolean>(false);
    const [currentUserMessage, setCurrentUserMessage] = useState<string>('');
    const [agentResponse, setAgentResponse] = useState<string>('');
    const [isAgentLoading, setIsAgentLoading] = useState<boolean>(false);
    const [messages, setMessages] = useState<Message[]>(() => {
        const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
        return saved
            ? JSON.parse(saved)
            : [{ role: 'assistant', content: 'Hi! Select a pattern to get started.', id: uuid(), animate: false }];
    });

 
    useEffect(() => {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages));
    }, [messages]);

    useEffect(() => {
        if (selectedPattern !== PATTERNS.NONE) {
            const patternMessages: PatternMessages = {
                [PATTERNS.SLIM_A2A]: 'Hi! How can I assist you?',
                [PATTERNS.SLIM_MULTI_A2A]: 'Hi, you are having a conversation with the supervisor. How can I help you?',
                [PATTERNS.IDENTITY]: 'Hi! How can I assist you?'
            };
            
            setMessages([{ 
                role: 'assistant', 
                content: patternMessages[selectedPattern], 
                id: uuid(), 
                animate: false 
            }]);
            
            setCurrentUserMessage('');
            setAgentResponse('');
            setIsAgentLoading(false);
        }
    }, [selectedPattern]);

    const handleCoffeeGraderSelect = (query: string) => {
        handleDropdownSelect(query);
    };

  
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
        
        const userMessage: Message = {
            role: 'user',
            content: query,
            id: uuid(),
            animate: true
        };
        
        const loadingMessage: Message = {
            role: 'assistant',
            content: '...',
            id: uuid(),
            animate: true
        };
        
        setMessages(prev => [...prev, userMessage, loadingMessage]);
        setButtonClicked(true);

        try {
            const response = await sendMessage(query);
            handleApiResponse(response, false);
        } catch (error) {
            console.error('API Error:', error);
            handleApiResponse('Sorry, I encountered an error.', true);
        }
    };

    return (
        <div className="flex flex-col w-screen h-screen overflow-hidden bg-primary-bg">
            <Navigation 
                selectedPattern={selectedPattern}
                onPatternChange={setSelectedPattern}
            />

            <div className="flex-grow flex flex-col bg-primary-bg">
                {selectedPattern === PATTERNS.NONE ? (
                    <PatternEmptyState />
                ) : (
                    <div className="flex-grow relative">
                        <MainArea 
                            pattern={selectedPattern}
                            buttonClicked={buttonClicked}
                            setButtonClicked={setButtonClicked}
                            aiReplied={aiReplied}
                            setAiReplied={setAiReplied}
                        />
                    </div>
                )}
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
                                        <div className="font-['Inter'] font-normal text-sm leading-5 text-white whitespace-pre-wrap">
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
                
                <BottomChat
                    messages={messages}
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                    setAiReplied={setAiReplied}
                    isBottomLayout={true}
                    showCoffeeDropdown={selectedPattern === PATTERNS.SLIM_A2A}
                    showBuyerDropdowns={selectedPattern === PATTERNS.SLIM_MULTI_A2A}
                    onCoffeeGraderSelect={handleCoffeeGraderSelect}
                    onDropdownSelect={handleDropdownSelect}
                    onApiResponse={handleApiResponse}
                />
            </div>
        </div>
    );
};

export default App;
