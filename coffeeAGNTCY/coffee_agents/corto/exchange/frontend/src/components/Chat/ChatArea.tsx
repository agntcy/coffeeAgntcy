/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';
import { Message } from '@/types/Message';
import airplaneSvg from '@/assets/airplane.svg';
import CoffeeGraderDropdown from './CoffeeGraderDropdown';
import { useAgentAPI } from '@/hooks/useAgentAPI';
import UserMessage from './UserMessage';
import AgentIcon from '@/assets/Coffee_Icon.svg';

interface ChatAreaProps {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    setButtonClicked: (clicked: boolean) => void;
    setAiReplied: (replied: boolean) => void;
    isBottomLayout: boolean;
    showCoffeeDropdown?: boolean;
    onCoffeeGraderSelect?: (query: string) => void;
    onDropdownSelect?: (query: string) => void;
    onUserInput?: (query: string) => void;
    onApiResponse?: (response: string, isError?: boolean) => void;
    currentUserMessage?: string;
    agentResponse?: string;
    isAgentLoading?: boolean;
}

const ChatArea: React.FC<ChatAreaProps> = ({ 
    setMessages, 
    setButtonClicked, 
    setAiReplied, 
    isBottomLayout,
    onDropdownSelect,
    onUserInput,
    onApiResponse,
    currentUserMessage,
    agentResponse,
    isAgentLoading
}) => {
    const [content, setContent] = useState<string>("");
    const { loading, sendMessageWithCallback } = useAgentAPI();

    const handleDropdownQuery = (query: string) => {
        if (onDropdownSelect) {
            onDropdownSelect(query);
        }
        processMessageWithQuery(query);
    };

    const processMessageWithQuery = async (messageContent: string): Promise<void> => {
        await sendMessageWithCallback(
            messageContent,
            setMessages,
            {
                onStart: () => {
                    setContent("");
                    setButtonClicked(true);
                },
                onSuccess: (response) => {
                    setAiReplied(true);
                    if (onApiResponse) {
                        onApiResponse(response, false);
                    }
                },
                onError: (error) => {
                    // Log error properly instead of using console.error
                    if (process.env.NODE_ENV === 'development') {
                        console.warn('API Error:', error);
                    }
                    if (onApiResponse) {
                        onApiResponse('Sorry, I encountered an error.', true);
                    }
                }
            }
        );
    };

    const processMessage = async (): Promise<void> => {
        if (onUserInput) {
            onUserInput(content);
        }
        await processMessageWithQuery(content);
        setContent("");
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            processMessage();
        }
    };

    if (!isBottomLayout) {
        return null;
    }

    return (
        <div className="flex flex-col justify-center items-center px-4 sm:px-8 md:px-16 lg:px-[120px] py-4 gap-2 w-full bg-[#2E3E57]" style={{ minHeight: currentUserMessage ? 'auto' : '120px' }}>
            
            {currentUserMessage && (
                <div className="flex flex-col gap-3 w-full max-w-[880px] mb-4">
                    <UserMessage content={currentUserMessage} />
                    {(isAgentLoading || agentResponse) && (
                        <div className="flex flex-row items-start gap-1 w-full">
                            <div className="flex justify-center items-center w-10 h-10 bg-[#00142B] rounded-full flex-none">
                                <img src={AgentIcon} alt="Agent" className="w-[22px] h-[22px]" />
                            </div>
                            <div className="flex flex-col justify-center items-start p-1 px-2 flex-1 max-w-[calc(100%-3rem)] rounded">
                                <div className="font-inter font-normal text-sm leading-5 text-white whitespace-pre-wrap break-words">
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
            )}
          
            <div className="flex flex-row items-start p-0 gap-2 w-auto h-9 relative z-10 w-full max-w-[880px]">
                <CoffeeGraderDropdown
                    visible={true}
                    onSelect={handleDropdownQuery}
                />
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center p-0 gap-4 w-full max-w-[880px]">
                <div className="box-border flex flex-row items-center py-[5px] px-0 flex-1 h-11 bg-[#1A2432] border border-[#1E2939] rounded max-w-[814px]">
                    <div className="flex flex-row items-center py-[7px] px-4 gap-[10px] w-full h-[34px]">
                        <input
                            className="flex-1 h-5 font-cisco font-medium text-[15px] leading-5 tracking-[0.005em] text-[#59616B] bg-transparent border-none outline-none focus:text-[#FBFCFE] min-w-0"
                            placeholder="Type a prompt to interact with the agents"
                            value={content}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setContent(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={loading}
                        />
                    </div>
                </div>
                <div className="flex flex-row items-start p-0 w-[50px] h-11 flex-none">
                    <button 
                        onClick={!content.trim() || loading ? undefined : processMessage}
                        disabled={!content.trim() || loading}
                        className="flex flex-row justify-center items-center py-[15px] px-4 gap-[10px] w-[50px] h-11 bg-gradient-to-r from-[#834DD7] via-[#7670D5] to-[#58C0D0] rounded-md border-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
                        <img src={airplaneSvg} alt="Send" className="w-[18px] h-[18px]" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatArea;
