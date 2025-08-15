/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';
import { Message } from '@/types/Message';
import airplaneSvg from '@/assets/airplane.svg';
import CoffeeGraderDropdown from './CoffeeGraderDropdown';
import { useAgentAPI } from '@/hooks/useAgentAPI';

interface ChatAreaProps {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    setButtonClicked: (clicked: boolean) => void;
    setAiReplied: (replied: boolean) => void;
    isBottomLayout: boolean;
    showCoffeeDropdown?: boolean;
    onCoffeeGraderSelect?: (query: string) => void;
    onDropdownSelect?: (query: string) => void;
    onApiResponse?: (response: string, isError?: boolean) => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({ 
    setMessages, 
    setButtonClicked, 
    setAiReplied, 
    isBottomLayout,
    onDropdownSelect,
    onApiResponse
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
        await processMessageWithQuery(content);
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
        <div className="flex flex-col items-center justify-center p-2 gap-1 w-full min-h-[76px] box-border relative">
          
      
       

            <div className="flex justify-start items-center w-[830px] max-w-full py-0 relative z-10 mx-auto">
                <CoffeeGraderDropdown
                    visible={true}
                    onSelect={handleDropdownQuery}
                />
            </div>

            <div className="flex flex-row items-center justify-center p-0 gap-4 w-[830px] max-w-full h-11 mx-auto">
                <div className="box-border flex flex-row items-center py-[5px] px-0 w-[764px] h-11 bg-[#1A2432] border border-[#1E2939] rounded flex-grow">
                    <div className="flex flex-row items-center py-[7px] px-4 gap-[10px] w-[764px] h-[34px] flex-grow">
                        <input
                            className="w-[732px] h-5 font-['CiscoSansTT','Inter',sans-serif] font-medium text-[15px] leading-5 tracking-[0.005em] text-[#59616B] bg-transparent border-none outline-none flex-grow focus:text-[#FBFCFE]"
                            placeholder="Describe what you are looking for"
                            value={content}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setContent(e.target.value)}
                            onKeyDown={handleKeyDown}
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
