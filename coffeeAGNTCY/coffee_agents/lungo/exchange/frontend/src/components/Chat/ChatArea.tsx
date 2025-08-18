/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';
import { Message } from '@/App';
import CoffeeGraderDropdown from './Prompts/CoffeeGraderDropdown';
import airplaneSvg from '@/assets/airplane.svg';
import CoffeePromptsDropdown from './Prompts/CoffeePromptsDropdown';
import { useAgentAPI } from '@/hooks/useAgentAPI';
import UserMessage from './UserMessage';
import AgentIcon from '@/assets/Coffee_Icon.svg';
import { cn } from '@/lib/utils';


interface ChatAreaProps {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    setButtonClicked: (clicked: boolean) => void;
    setAiReplied: (replied: boolean) => void;
    isBottomLayout: boolean;
    showCoffeeDropdown?: boolean;
    showCoffeePrompts?: boolean;
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
    showCoffeeDropdown = false,
    showCoffeePrompts = false,
    onDropdownSelect,
    onUserInput,
    onApiResponse,
    currentUserMessage,
    agentResponse,
    isAgentLoading
}) => {
    const [content, setContent] = useState<string>("");
    const [loading, setLoading] = useState<boolean>(false);
    const { sendMessageWithCallback } = useAgentAPI();

    const handleDropdownQuery = (query: string) => {
        if (onDropdownSelect) {
            onDropdownSelect(query);
        }
        processMessageWithQuery(query);
    };

    const processMessageWithQuery = async (messageContent: string): Promise<void> => {
        if (!messageContent.trim()) return;

        setContent(""); 
        setLoading(true);
        setButtonClicked(true);

        await sendMessageWithCallback(
            messageContent,
            setMessages,
            {
                onSuccess: (response) => {
                    setAiReplied(true);
                    if (onApiResponse) {
                        onApiResponse(response, false);
                    }
                },
                onError: (error) => {
                    console.error('Error:', error);
                    if (onApiResponse) {
                        onApiResponse('Sorry, I encountered an error.', true);
                    }
                }
            }
        );

        setLoading(false);
    };

    const processMessage = async (): Promise<void> => {
        if (onUserInput) {
            onUserInput(content);
        }
        await processMessageWithQuery(content);
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>): void => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            processMessage();
        }
    };

    if (!isBottomLayout) {
        return null;
    }

    return (
        <div className={cn(
            "flex flex-col justify-center items-start px-[120px] py-4 gap-2 w-[1120px] bg-[#2E3E57]",
            currentUserMessage ? "min-h-auto" : "min-h-[120px]"
        )}>
            
            {currentUserMessage && (
                <div className="flex flex-col gap-3 w-[880px] mb-4">
                    <UserMessage content={currentUserMessage} />
                    {(isAgentLoading || agentResponse) && (
                        <div className="flex flex-row items-start gap-1 w-[880px]">
                            <div className="flex justify-center items-center w-10 h-10 bg-[#00142B] rounded-full">
                                <img src={AgentIcon} alt="Agent" className="w-[22px] h-[22px] filter brightness-0 invert" />
                            </div>
                            <div className="flex flex-col justify-center items-start p-1 px-2 w-[814px] rounded">
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
            )}
          
            {showCoffeeDropdown && (
                <div className="flex flex-row items-start p-0 gap-2 w-[166px] h-9 relative z-10">
                    <CoffeeGraderDropdown 
                        visible={true}
                        onSelect={handleDropdownQuery}
                    />
                </div>
            )}

            {showCoffeePrompts && (
                <div className="flex flex-row items-start p-0 gap-2 w-[166px] h-9 relative z-10">
                    <CoffeePromptsDropdown 
                         visible={true}
            onSelect={handleDropdownQuery} 
                    />
                </div>
            )}
            
            <div className="flex flex-row items-center p-0 gap-4 w-[880px] h-11">
                <div className="box-border flex flex-row items-center py-[5px] px-0 w-[814px] h-11 bg-[#1A2432] border border-[#1E2939] rounded">
                    <div className="flex flex-row items-center py-[7px] px-4 gap-[10px] w-[814px] h-[34px]">
                        <input
                            className="w-[782px] h-5 font-cisco font-medium text-[15px] leading-5 tracking-[0.005em] text-[#59616B] bg-transparent border-none outline-none focus:text-[#FBFCFE]"
                            placeholder="Type a prompt to interact with the agents"
                            value={content}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setContent(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={loading}
                        />
                    </div>
                </div>
                <div className="flex flex-row items-start p-0 w-[50px] h-11">
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
