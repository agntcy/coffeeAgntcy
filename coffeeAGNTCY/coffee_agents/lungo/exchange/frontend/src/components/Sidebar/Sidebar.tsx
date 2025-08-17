/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';
import { ChevronUp } from 'lucide-react';
import { PatternType, PATTERNS } from '@/App';
import SidebarItem from './sidebarItem';
import SidebarDropdown from './SidebarDropdown';

interface SidebarProps {
  selectedPattern: PatternType;
  onPatternChange: (pattern: PatternType) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ selectedPattern, onPatternChange }) => {
  const [isBuyerExpanded, setIsBuyerExpanded] = useState(true); // Auto-expanded
  const [isTransportExpanded, setIsTransportExpanded] = useState(true);

  const handleBuyerToggle = () => {
    setIsBuyerExpanded(!isBuyerExpanded);
  };

  const handleTransportToggle = () => {
    setIsTransportExpanded(!isTransportExpanded);
  };

  return (
    <div 
      className="w-[320px] h-full bg-primary-bg font-inter box-border flex flex-col items-start py-4 px-0 border-r border-[#0D274D] flex-none order-0 self-stretch flex-grow-0"
    >
      <div 
        className="bg-primary-bg flex flex-col items-start px-4 py-0 gap-5 w-[320px] h-full flex-1"
      >


        <div 
          className="flex flex-col items-start font-inter p-0 w-[288px] h-[524px] flex-none order-1 self-stretch flex-grow-0"
        >
          <div 
            className="flex flex-col items-start font-inter p-0 w-[288px] h-[72px] flex-none order-0 self-stretch flex-grow-0"
          >
          <div 
            className="flex flex-row items-start cursor-pointer bg-primary-bg w-[288px] h-9 py-2 px-0 gap-2 flex-none order-0 self-stretch flex-grow-0"
            onClick={handleBuyerToggle}
          >
            <span className="w-[288px] h-5 font-inter font-normal text-sm leading-5 tracking-[0.25px] text-white flex-none order-1 flex-grow">
              Conversation: Coffee Buying
            </span>
            <ChevronUp 
              className={`transition-transform hidden w-5 h-5 flex-none order-2 flex-grow-0 ${
                isBuyerExpanded ? 'rotate-0' : 'rotate-180'
              }`}
            />
          </div>
          
          {isBuyerExpanded && (
            <div 
              className="flex flex-col items-start w-[288px] h-[452px] p-0 gap-2 flex-none order-1 self-stretch flex-grow-0"
            >
              <div 
                className="flex flex-col items-start p-0 w-[288px] h-36 flex-none order-0 self-stretch flex-grow-0"
              >
                <div 
                  className="flex items-center w-[288px] h-9 gap-2 py-2 px-5"
                >
                  <span className="w-[208px] h-5 opacity-100 font-inter font-normal text-sm leading-5 tracking-[0.25px] text-white">
                    Agentic Patterns
                  </span>
                </div>
                
                <div>
                  <SidebarDropdown
                    title="Transport"
                    isExpanded={isTransportExpanded}
                    onToggle={handleTransportToggle}
                    isNested={true}
                  >
                    <SidebarItem
                      title="Multi SLIM A2A"
                      isSelected={selectedPattern === PATTERNS.SLIM_MULTI_A2A}
                      onClick={() => onPatternChange(PATTERNS.SLIM_MULTI_A2A)}
                    />
                  </SidebarDropdown>
                </div>
              </div>
            </div>
          )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
