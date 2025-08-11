/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';
import { PATTERNS, PatternType } from '@/App';
import coffeeAgntcyLogo from '@/assets/coffeeAGNTCY_logo.svg';

interface NavigationProps {
    selectedPattern: PatternType;
    onPatternChange: (pattern: PatternType) => void;
}

interface Tab {
    id: PatternType;
    label: string;
}

const Navigation: React.FC<NavigationProps> = ({ selectedPattern, onPatternChange }) => {
    const tabs: Tab[] = [
        { id: PATTERNS.SLIM_A2A, label: 'SLIM A2A' },
        { id: PATTERNS.SLIM_MULTI_A2A, label: 'SLIM Multi A2A' },
        { id: PATTERNS.IDENTITY, label: 'Identity' }
    ];

    return (
        <div className="
            box-border flex flex-col items-start p-0 w-full h-[100px] 
            bg-[#F5F8FD] border-r border-[#DBE0E5] 
            flex-none order-0 self-stretch flex-grow-0
        ">
      
            <div className="
                box-border flex flex-row justify-between items-center 
                py-[10px] px-4 gap-2 w-full h-[52px] 
                bg-[#EFF3FC] border-b border-[#D5DFF7] 
                flex-none order-0 self-stretch flex-grow-0
            ">
                <div className="
                    flex flex-row items-center p-0 gap-2 ml-4 
                    w-40 h-[45px] flex-none order-0 flex-grow-0 opacity-100
                ">
                    <div className="
                        flex flex-row items-center p-0 gap-1 
                        w-40 h-[45px] flex-none order-0 flex-grow-0 opacity-100
                    ">
                        <div className="
                            flex justify-center items-center gap-0.5 
                            w-auto h-[42px] flex-none order-0 flex-grow-0 opacity-100
                        ">
                            <img 
                                src={coffeeAgntcyLogo} 
                                alt="Coffee AGNTCY Logo" 
                                className="w-40 h-full object-contain" 
                            />
                        </div>
                    </div>
                </div>
            </div>

       
            <div className="
                flex flex-row items-center py-2 px-4 gap-4 
                w-full h-12 border-b border-[#DBE0E5] 
                flex-none order-1 self-stretch flex-grow-0 opacity-100
            ">
                {tabs.map((tab: Tab) => (
                    <div 
                        key={tab.id}
                        className={`
                            flex flex-row items-center py-[9px] px-4 gap-[10px] 
                            ${tab.id === PATTERNS.SLIM_MULTI_A2A ? 'w-auto min-w-[140px]' : 'w-[99px]'} 
                            h-[38px] rounded-[20px] cursor-pointer 
                            flex-none order-0 flex-grow-0 opacity-100
                            shadow-[0px_-1px_0px_0px_#FFFFFF00_inset]
                            ${selectedPattern === tab.id ? 'bg-[#00142B]' : 'bg-transparent'}
                        `}
                        onClick={() => onPatternChange(tab.id)}
                    >
                        <div className="
                            flex flex-col items-center p-0 gap-0 
                            w-full h-full rounded-[20px] 
                            flex-none order-0 flex-grow-0 opacity-100
                        ">
                            <div className="
                                flex flex-row items-center justify-center p-0 gap-0 
                                h-5 flex-none order-0 flex-grow-0
                            ">
                                <div className={`
                                    h-5 font-[Inter] font-normal text-sm leading-5 tracking-[0.25px]
                                    flex-none order-0 flex-grow-0 opacity-100 text-center
                                    ${selectedPattern === tab.id ? 'text-white' : 'text-[#3C4551]'}
                                `}>
                                    {tab.label}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Navigation;
