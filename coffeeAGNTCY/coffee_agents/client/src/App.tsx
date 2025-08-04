/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState, useEffect } from 'react';
import { v4 as uuid } from 'uuid';
import { LOCAL_STORAGE_KEY } from '@/components/Chat/Messages';

import BottomChat from '@/components/Chat/BottomChat';
import CodePopUp from "@/components/MainArea/CodePopUp";

import Navigation from '@/components/Navigation/Navigation';
import PatternEmptyState from '@/components/MainArea/PatternEmptyState';
import MainArea from '@/components/MainArea/MainArea';

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

    const [selectedPattern, setSelectedPattern] = useState<PatternType>(PATTERNS.NONE);
    const [aiReplied, setAiReplied] = useState<boolean>(false);
    const [buttonClicked, setButtonClicked] = useState<boolean>(false);
    const [showCode, setShowCode] = useState<boolean>(false);
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
        }
    }, [selectedPattern]);

    const handleCoffeeGraderSelect = (query: string) => {
        const newMessage: Message = {
            role: 'user',
            content: query,
            id: uuid(),
            animate: true
        };
        setMessages(prev => [...prev, newMessage]);
        setButtonClicked(true);
    };

    return (
        <div className="flex flex-col w-screen h-screen overflow-hidden bg-primary-bg">
            <Navigation 
                selectedPattern={selectedPattern}
                onPatternChange={setSelectedPattern}
            />

            <div className="flex-grow flex flex-col bg-primary-bg">
                <div className="box-border flex flex-row justify-between items-center p-4 gap-2.5 w-full h-[52px] bg-[#23282E] border-b border-[#1A1F27] flex-none self-stretch flex-grow-0">
                    <button className="flex flex-row justify-center items-center p-0 gap-1 w-36 h-5 rounded-md border-none bg-transparent cursor-pointer flex-none order-0 flex-grow-0">
                        <span className="w-36 h-5 font-['Inter'] font-bold text-sm leading-5 text-[#FBFCFE] flex-none order-1 flex-grow-0">AGNTCY Graph View</span>
                    </button>
                    <button 
                        className="flex flex-row justify-center items-center p-0 gap-1 w-[81px] h-5 rounded-md border-none bg-transparent cursor-pointer flex-none order-1 flex-grow-0 ml-auto transition-all duration-200 ease-in-out"
                        onClick={() => setShowCode(!showCode)}
                    >
                        <div className={`flex flex-row items-center p-[3px] gap-2 w-10 h-5 rounded-[14px] flex-none order-0 flex-grow-0 opacity-100 transition-colors duration-200 ease-in-out relative ${
                            showCode ? 'bg-primary-blue' : 'bg-[#D0D4D9]'
                        }`}>
                            <div className={`w-[14px] h-[14px] bg-white rounded flex-none order-0 flex-grow-0 transition-transform duration-200 ease-in-out absolute left-[3px] ${
                                showCode ? 'transform translate-x-5' : ''
                            }`}></div>
                        </div>
                        <span className={`w-[37px] h-5 font-['Inter'] font-bold text-sm leading-5 flex-none order-1 flex-grow-0 transition-colors duration-200 ease-in-out ${
                            showCode ? 'text-primary-blue' : 'text-[#649EF5]'
                        }`}>Code</span>
                    </button>
                </div>

                {selectedPattern === PATTERNS.NONE ? (
                    <PatternEmptyState />
                ) : (
                    <div className="flex-grow flex flex-col bg-primary-bg">
                        <div className="relative">
                            <CodePopUp 
                                showCode={showCode}
                                selectedPattern={selectedPattern}
                                onClose={() => setShowCode(false)}
                            />
                        </div>
                        <div className="flex-grow relative">
                            <MainArea 
                                pattern={selectedPattern}
                                buttonClicked={buttonClicked}
                                setButtonClicked={setButtonClicked}
                                aiReplied={aiReplied}
                                setAiReplied={setAiReplied}
                            />
                        </div>
                    </div>
                )}
            </div>

            <div className="flex flex-col justify-center items-center p-0 gap-0 w-full min-h-[76px] max-h-[200px] bg-[#2E3E57] flex-none self-stretch flex-grow-0 min-w-[1440px] box-border overflow-visible">
                <BottomChat
                    messages={messages}
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                    setAiReplied={setAiReplied}
                    isBottomLayout={true}
                    showCoffeeDropdown={selectedPattern === PATTERNS.SLIM_A2A}
                    showBuyerDropdowns={selectedPattern === PATTERNS.SLIM_MULTI_A2A}
                    onCoffeeGraderSelect={handleCoffeeGraderSelect}
                />
            </div>
        </div>
    );
};

export default App;
