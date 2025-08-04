/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState, useRef, useEffect } from 'react';

interface CoffeeGraderDropdownProps {
    visible: boolean;
    onSelect: (query: string) => void;
}

const CoffeeGraderDropdown: React.FC<CoffeeGraderDropdownProps> = ({ visible, onSelect }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const dropdownItems = [
        "What are the flavor profiles of Ethiopian coffee?",
        "Where can I get the best coffee with flavors like Ethiopian?"
    ];

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

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
        <div className="relative inline-block" ref={dropdownRef}>
            <div 
                className={`
                    box-border flex flex-row items-center p-2 gap-1 w-auto min-w-32 h-9 
                    bg-[#1A2432] border border-[#DDDDDD] rounded cursor-pointer 
                    transition-colors duration-200 ease-in-out
                    hover:bg-[#1F2A3A]
                    ${isOpen ? 'bg-[#1F2A3A]' : ''}
                `}
                onClick={handleToggle}
            >
                <div className="flex flex-col items-start p-0 gap-1 flex-1 h-5 flex-none order-0 flex-grow-0">
                    <div className="
                        w-full h-5 font-cisco font-normal text-sm leading-5 tracking-[0%] 
                        text-white flex-none order-0 self-stretch flex-grow-0 
                        whitespace-nowrap 
                    ">
                        Coffee Grader
                    </div>
                </div>
                <div className="w-6 h-6 flex-none order-1 flex-grow-0 relative flex items-center justify-center">
                    <div 
                        className={`
                            w-[11.15px] h-[6.55px] bg-[#E8E9EA] transition-transform duration-300 ease-in-out
                            ${isOpen ? 'rotate-180' : ''}
                        `}
                        style={{clipPath: 'polygon(50% 100%, 0% 0%, 100% 0%)'}}
                    ></div>
                </div>
            </div>
            
            <div className={`
                absolute bottom-full left-0 mb-1 w-[269px] max-h-28 
                bg-[#23282E] border border-[#D5DFF7] rounded-md 
                shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] p-0.5 z-[1000] 
                overflow-y-auto
                ${isOpen ? 'block animate-fadeInDropdown' : 'hidden'}
            `}>
                {dropdownItems.map((item, index) => (
                    <div 
                        key={index}
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
    );
};

export default CoffeeGraderDropdown;
