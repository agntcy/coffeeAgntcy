/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState, useRef, useEffect } from 'react';

interface BuyerPurchaserDropdownProps {
    visible: boolean;
    onSelect: (query: string) => void;
}

const BuyerPurchaserDropdowns: React.FC<BuyerPurchaserDropdownProps> = ({ visible, onSelect }) => {
    const [isBuyerOpen, setIsBuyerOpen] = useState(false);
    const [isPurchaserOpen, setIsPurchaserOpen] = useState(false);
    const buyerDropdownRef = useRef<HTMLDivElement>(null);
    const purchaserDropdownRef = useRef<HTMLDivElement>(null);

    const buyerDropdownItems = [
        "What yield do the farms have?",
        "What is the current inventory?", 
        "I'd like to buy 200 lbs quantity of coffee and who can fulfil it?",
        "List all the coffee farms"
    ];

    const purchaserDropdownItems = [
        "I'd like to buy 200 lbs quantity of coffee at USD 500 price from Colombia",
        "What is the status of my purchase?",
        "Who are verified purchasers or suppliers?"
    ];

 
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as Node;
            
            // Check if click is outside buyer dropdown
            if (isBuyerOpen && buyerDropdownRef.current && !buyerDropdownRef.current.contains(target)) {
                setIsBuyerOpen(false);
            }
            
            // Check if click is outside purchaser dropdown
            if (isPurchaserOpen && purchaserDropdownRef.current && !purchaserDropdownRef.current.contains(target)) {
                setIsPurchaserOpen(false);
            }
        };

        const handleEscapeKey = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setIsBuyerOpen(false);
                setIsPurchaserOpen(false);
            }
        };

        // Always listen for clicks when component is visible and any dropdown is open
        if (visible && (isBuyerOpen || isPurchaserOpen)) {
            document.addEventListener('mousedown', handleClickOutside, true); // Use capture phase
            document.addEventListener('keydown', handleEscapeKey);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside, true);
            document.removeEventListener('keydown', handleEscapeKey);
        };
    }, [isBuyerOpen, isPurchaserOpen, visible]);

 
    const handleBuyerToggle = () => {
        setIsBuyerOpen(!isBuyerOpen);
        setIsPurchaserOpen(false); 
    };

    const handlePurchaserToggle = () => {
        setIsPurchaserOpen(!isPurchaserOpen);
        setIsBuyerOpen(false);
    };

    const handleItemClick = (item: string) => {
        onSelect(item);
        setIsBuyerOpen(false);
        setIsPurchaserOpen(false);
    };

    if (!visible) {
        return null;
    }

    return (
        <div className="flex gap-3 items-center">
          
            <div className="relative inline-block" ref={buyerDropdownRef}>
                <div 
                    className={`
                        box-border flex flex-row items-center p-2 gap-1 w-auto min-w-32 h-9 
                        bg-[#1A2432] border border-[#DDDDDD] rounded cursor-pointer 
                        transition-colors duration-200 ease-in-out
                        hover:bg-[#1F2A3A]
                        ${isBuyerOpen ? 'bg-[#1F2A3A]' : ''}
                    `}
                    onClick={handleBuyerToggle}
                >
                    <div className="flex flex-col items-start p-0 gap-1 flex-1 h-5 flex-none order-0 flex-grow-0">
                        <div className="
                            w-full h-5 font-cisco font-normal text-sm leading-5 tracking-[0%] 
                            text-white flex-none order-0 self-stretch flex-grow-0 
                            whitespace-nowrap
                        ">
                            Coffee Buyer
                        </div>
                    </div>
                    <div className="w-6 h-6 flex-none order-1 flex-grow-0 relative flex items-center justify-center">
                        <div 
                            className={`
                                w-[11.15px] h-[6.55px] bg-[#E8E9EA] transition-transform duration-300 ease-in-out
                                ${isBuyerOpen ? 'rotate-180' : ''}
                            `}
                            style={{clipPath: 'polygon(50% 100%, 0% 0%, 100% 0%)'}}
                        ></div>
                    </div>
                </div>
                
              
                <div className={`
                    absolute bottom-full left-0 mb-1 w-[350px] max-h-40 
                    bg-[#23282E] border border-[#D5DFF7] rounded-md 
                    shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] p-0.5 z-[1000] 
                    overflow-y-auto
                    ${isBuyerOpen ? 'block animate-fadeInDropdown' : 'hidden'}
                `}>
                    {buyerDropdownItems.map((item, index) => (
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

            <div className="relative inline-block" ref={purchaserDropdownRef}>
            
                <div 
                    className={`
                        box-border flex flex-row items-center p-2 gap-1 w-auto min-w-32 h-9 
                        bg-[#1A2432] border border-[#DDDDDD] rounded cursor-pointer 
                        transition-colors duration-200 ease-in-out
                        hover:bg-[#1F2A3A]
                        ${isPurchaserOpen ? 'bg-[#1F2A3A]' : ''}
                    `}
                    onClick={handlePurchaserToggle}
                >
                    <div className="flex flex-col items-start p-0 gap-1 flex-1 h-5 flex-none order-0 flex-grow-0">
                        <div className="
                            w-full h-5 font-cisco font-normal text-sm leading-5 tracking-[0%] 
                            text-white flex-none order-0 self-stretch flex-grow-0 
                            whitespace-nowrap
                        ">
                            Coffee Purchaser
                        </div>
                    </div>
                    <div className="w-6 h-6 flex-none order-1 flex-grow-0 relative flex items-center justify-center">
                        <div 
                            className={`
                                w-[11.15px] h-[6.55px] bg-[#E8E9EA] transition-transform duration-300 ease-in-out
                                ${isPurchaserOpen ? 'rotate-180' : ''}
                            `}
                            style={{clipPath: 'polygon(50% 100%, 0% 0%, 100% 0%)'}}
                        ></div>
                    </div>
                </div>
                
              
                <div className={`
                    absolute bottom-full left-0 mb-1 w-[350px] max-h-40 
                    bg-[#23282E] border border-[#D5DFF7] rounded-md 
                    shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] p-0.5 z-[1000] 
                    overflow-y-auto
                    ${isPurchaserOpen ? 'block animate-fadeInDropdown' : 'hidden'}
                `}>
                    {purchaserDropdownItems.map((item, index) => (
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

        </div>
    );
};

export default BuyerPurchaserDropdowns;