/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';
import { v4 as uuid } from 'uuid';
import axios from 'axios';
import { Message } from '@/App';
import { Role } from '@/utils/const';
import CoffeeGraderDropdown from './Prompts/CoffeeGraderDropdown';
import airplaneSvg from '@/assets/airplane.svg';
import BuyerPurchaserDropdowns from './Prompts/BuyerPurchaserDropdown';
const DEFAULT_EXCHANGE_APP_API_URL = 'http://0.0.0.0:8000';


interface BottomChatProps {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    setButtonClicked: (clicked: boolean) => void;
    setAiReplied: (replied: boolean) => void;
    isBottomLayout: boolean;
    showCoffeeDropdown?: boolean;
    showBuyerDropdowns?: boolean;
    onCoffeeGraderSelect?: (query: string) => void;
    onDropdownSelect?: (query: string) => void;
    onApiResponse?: (response: string, isError?: boolean) => void;
}

interface ApiResponse {
    response: string;
}

const BottomChat: React.FC<BottomChatProps> = ({ 

    setMessages, 
    setButtonClicked, 
    setAiReplied, 
    isBottomLayout,
    showCoffeeDropdown = false,
    showBuyerDropdowns = false,
    onDropdownSelect,
    onApiResponse
}) => {
    const [content, setContent] = useState<string>("");
    const [loading, setLoading] = useState<boolean>(false);

    const handleDropdownQuery = (query: string) => {
        if (onDropdownSelect) {
            onDropdownSelect(query);
        }
        processMessageWithQuery(query);
    };

    const processMessageWithQuery = async (messageContent: string): Promise<void> => {
        if (!messageContent.trim()) return;

        const userMessage: Message = {
            role: Role.USER,
            content: messageContent,
            id: uuid(),
            animate: false,
        };

        const loadingMessage: Message = {
            role: 'assistant',
            content: '...',
            id: uuid(),
            animate: true,
        };

        setMessages((prevMessages: Message[]) => [...prevMessages, userMessage, loadingMessage]);
        setContent(""); 
        setLoading(true);
        setButtonClicked(true);

        try {
            const response = await axios.post<ApiResponse>(`${DEFAULT_EXCHANGE_APP_API_URL}/agent/prompt`, {
                prompt: messageContent, 
            });

            setMessages((prevMessages: Message[]) => {
                const updatedMessages = [...prevMessages];
                updatedMessages[updatedMessages.length - 1] = {
                    role: 'assistant',
                    content: response.data.response,
                    id: uuid(),
                    animate: true,
                };
                return updatedMessages;
            });
            setAiReplied(true);
            
           
            if (onApiResponse) {
                onApiResponse(response.data.response, false);
            }
        } catch (error) {
            console.error('Error:', error);
            setMessages((prevMessages: Message[]) => {
                const updatedMessages = [...prevMessages];
                updatedMessages[updatedMessages.length - 1] = {
                    role: 'assistant',
                    content: 'Sorry, I encountered an error.',
                    id: uuid(),
                    animate: false,
                };
                return updatedMessages;
            });
            
            if (onApiResponse) {
                onApiResponse('Sorry, I encountered an error.', true);
            }
        } finally {
            setLoading(false);
        }
    };

    const processMessage = async (): Promise<void> => {
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
        <div className="flex flex-col items-center justify-center p-4 gap-1 w-full min-h-[76px] box-border relative">
          
            {showCoffeeDropdown && (
                <div className="flex justify-start items-center w-[830px] max-w-full py-1 relative z-10 mx-auto">
                    <CoffeeGraderDropdown 
                        visible={true}
                        onSelect={handleDropdownQuery}
                    />
                </div>
            )}

            {showBuyerDropdowns && (
                <div className="w-[830px] max-w-full py-1 relative z-10 mx-auto">
                    <BuyerPurchaserDropdowns 
                         visible={true}
            onSelect={handleDropdownQuery} 
                    />
                </div>
            )}
            
            <div className="flex flex-row items-center justify-center p-0 gap-4 w-[830px] max-w-full h-11 mx-auto">
                <div className="box-border flex flex-row items-center py-[5px] px-0 w-[764px] h-11 bg-[#1A2432] border border-[#1E2939] rounded flex-grow">
                    <div className="flex flex-row items-center py-[7px] px-4 gap-[10px] w-[764px] h-[34px] flex-grow">
                        <input
                            className="w-[732px] h-5 font-['CiscoSansTT','Inter',sans-serif] font-medium text-[15px] leading-5 tracking-[0.005em] text-[#59616B] bg-transparent border-none outline-none flex-grow focus:text-[#FBFCFE]"
                            placeholder="Describe what you are looking for"
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

export default BottomChat;
