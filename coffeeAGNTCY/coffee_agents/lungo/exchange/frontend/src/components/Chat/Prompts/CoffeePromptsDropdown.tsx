/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState, useRef, useEffect } from 'react';

interface CoffeePromptsDropdownProps {
    visible: boolean;
    onSelect: (query: string) => void;
}

const CoffeePromptsDropdown: React.FC<CoffeePromptsDropdownProps> = ({ visible, onSelect }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);


    const buyerPrompts = [
        "What yield do the farms have?",
        "What is the current inventory?", 
        "I'd like to buy 200 lbs quantity of coffee and who can fulfil it?",
        "List all the coffee farms"
    ];

    const purchaserPrompts = [
        "I'd like to buy 200 lbs quantity of coffee at USD 500 price from Colombia",
        "What is the status of my purchase?",
        "Who are verified purchasers or suppliers?"
    ];

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as Node;
            
            if (isOpen && dropdownRef.current && !dropdownRef.current.contains(target)) {
                setIsOpen(false);
            }
        };

        const handleEscapeKey = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setIsOpen(false);
            }
        };

        if (visible && isOpen) {
            document.addEventListener('mousedown', handleClickOutside, true);
            document.addEventListener('keydown', handleEscapeKey);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside, true);
            document.removeEventListener('keydown', handleEscapeKey);
        };
    }, [isOpen, visible]);

    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    const handleItemClick = (item: string) => {
        onSelect(item);
        setIsOpen(false);
    };

    if (!visible) {
        return null;
    }

    return (
        <div className="flex gap-3 items-center">
            <div className="relative inline-block" ref={dropdownRef}>
                <div 
                    className={`
                        flex flex-row items-center p-2 gap-1 w-166 h-9
                        bg-[#1A2432] rounded-lg cursor-pointer 
                        transition-colors duration-200 ease-in-out
                        hover:bg-[#1F2A3A]
                        ${isOpen ? 'bg-[#1F2A3A]' : ''}
                    `}
                    onClick={handleToggle}
                >
                    <div className="flex flex-col items-start p-0 gap-1 w-122 h-5 flex-none order-0 flex-grow-0">
                        <div className="
                            w-122 h-5 font-cisco font-normal text-sm leading-5
                            text-[#FBFCFE] flex-none order-0 self-stretch flex-grow-0 
                            whitespace-nowrap
                        ">
                            Suggested Prompts
                        </div>
                    </div>
                    <div className="w-6 h-6 flex-none order-1 flex-grow-0 relative">
                        <div 
                            className={`
                                absolute left-[26.77%] right-[26.77%] top-[36.35%] bottom-[36.35%]
                                bg-[#59616B] transition-transform duration-300 ease-in-out
                                ${isOpen ? 'rotate-180' : ''}
                            `}
                            style={{clipPath: 'polygon(50% 100%, 0% 0%, 100% 0%)'}}
                        ></div>
                    </div>
                </div>
                
                <div className={`
                    absolute bottom-full left-0 mb-1 w-269 h-[365px] 
                    bg-[#23282E] border border-[#D5DFF7] rounded-[6px] 
                    shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] px-[2px] py-0 z-[1000] 
                    overflow-y-auto opacity-100
                    ${isOpen ? 'block animate-fadeInDropdown' : 'hidden'}
                `}>
                    <div className="px-2 py-2">
                        <div 
                            className="font-inter font-normal text-sm leading-5 tracking-[0%] text-[#889099] mb-2 px-2"
                            style={{
                                width: '245px',
                                height: '20px',
                                opacity: 1
                            }}
                        >
                            BUYER
                        </div>
                        {buyerPrompts.map((item, index) => (
                            <div 
                                key={`buyer-${index}`}
                                className="
                                    w-[calc(100%-4px)] min-h-10 py-[6px] px-2 my-0.5 mx-0.5
                                    bg-[#23282E] rounded cursor-pointer 
                                    transition-colors duration-200 ease-in-out
                                    hover:bg-[#2A3441] flex items-center
                                "
                                onClick={() => handleItemClick(item)}
                            >
                                <div className="
                                    w-full font-cisco font-normal text-sm leading-5 tracking-[0%] 
                                    text-white break-words
                                ">
                                    {item}
                                </div>
                            </div>
                        ))}
                    </div>

        
                    <div className="mx-2 border-t border-[#889099] my-2"></div>

               
                    <div className="px-2 py-2">
                        <div 
                            className="font-inter font-normal text-sm leading-5 tracking-[0%] text-[#889099] mb-2 w-[265px] h-[36px] gap-2 opacity-100 pt-2 pr-[10px] pb-2 pl-[10px] bg-[#23282E]"
                        >
                            PURCHASER
                        </div>
                        {purchaserPrompts.map((item, index) => (
                            <div 
                                key={`purchaser-${index}`}
                                className="
                                    w-[calc(100%-4px)] min-h-10 py-[6px] px-2 my-0.5 mx-0.5
                                    bg-[#23282E] rounded cursor-pointer 
                                    transition-colors duration-200 ease-in-out
                                    hover:bg-[#2A3441] flex items-center
                                "
                                onClick={() => handleItemClick(item)}
                            >
                                <div className="
                                    w-full font-cisco font-normal text-sm leading-5 tracking-[0%] 
                                    text-white break-words
                                ">
                                    {item}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CoffeePromptsDropdown;
