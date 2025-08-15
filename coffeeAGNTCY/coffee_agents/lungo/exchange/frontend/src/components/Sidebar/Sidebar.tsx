/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';
import { ChevronUp } from 'lucide-react';
import { PatternType, PATTERNS } from '@/App';
import SidebarSection from './SidebarSection';
import SidebarItem from './sidebarItem';
import SidebarDropdown from './SidebarDropdown';

interface SidebarProps {
  selectedPattern: PatternType;
  onPatternChange: (pattern: PatternType) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ selectedPattern, onPatternChange }) => {
  const [isGraderExpanded, setIsGraderExpanded] = useState(true); // Auto-expanded
  const [isBuyerExpanded, setIsBuyerExpanded] = useState(false);
  const [isTransportExpanded, setIsTransportExpanded] = useState(false);

  const handleGraderToggle = () => {
    setIsGraderExpanded(!isGraderExpanded);
  };

  const handleBuyerToggle = () => {
    setIsBuyerExpanded(!isBuyerExpanded);
  };

  const handleTransportToggle = () => {
    setIsTransportExpanded(!isTransportExpanded);
  };

  const handleAgentToAgentClick = () => {
    onPatternChange(PATTERNS.SLIM_A2A);
  };

  return (
    <div 
      className="w-[320px] h-full bg-primary-bg border-r border-black"
      style={{
        width: '320px',
        opacity: 1,
        borderRightWidth: '1px',
        borderRightColor: '#000000'
      }}
    >
      <div className="p-4">
        {/* Coffee Grader Conversation - Direct Structure like old version */}
        <div 
          className="flex items-center justify-between cursor-pointer w-72 h-9 gap-2 py-2 text-white text-sm font-normal leading-5"
          onClick={handleGraderToggle}
          style={{
            letterSpacing: '0.25px'
          }}
        >
          <span className="pl-2">
            Coffee Grader Conversation
          </span>
          <ChevronUp 
            className={`w-4 h-4 text-white transition-transform mr-2 ${
              isGraderExpanded ? 'rotate-0' : 'rotate-180'
            }`}
          />
        </div>
        {isGraderExpanded && (
          <div className="flex flex-col">
            <SidebarItem
              title="Agent to Agent"
              isSelected={selectedPattern === PATTERNS.SLIM_A2A}
              onClick={handleAgentToAgentClick}
            />
          </div>
        )}

        {/* Coffee Buyer Conversation Section */}
        <SidebarSection
          title="Coffee Buyer Conversation"
          isExpanded={isBuyerExpanded}
          onToggle={handleBuyerToggle}
        >
          <div className="flex flex-col items-start p-0 w-72 h-18 flex-none order-0 self-stretch grow-0">
            <div className="w-72 h-9 flex items-center pl-2 text-white text-sm font-normal leading-5"
                 style={{ letterSpacing: '0.25px' }}>
              Agentic Patterns
            </div>
            
            <SidebarDropdown
              title="Transport"
              isExpanded={isTransportExpanded}
              onToggle={handleTransportToggle}
            >
              <SidebarItem
                title="SLIM A2A"
                isSelected={selectedPattern === PATTERNS.SLIM_A2A}
                onClick={() => onPatternChange(PATTERNS.SLIM_A2A)}
              />
              <SidebarItem
                title="Multi SLIM A2A"
                isSelected={selectedPattern === PATTERNS.SLIM_MULTI_A2A}
                onClick={() => onPatternChange(PATTERNS.SLIM_MULTI_A2A)}
              />
            </SidebarDropdown>
          </div>
        </SidebarSection>
      </div>
    </div>
  );
};

export default Sidebar;
