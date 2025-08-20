/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';

interface SidebarProps {
  selectedView: 'coffee-grading' | 'agent-to-agent';
  onViewChange: (view: 'coffee-grading' | 'agent-to-agent') => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedView,
  onViewChange
}) => {
  const [isGradingExpanded, setIsGradingExpanded] = useState(true);

  const handleGradingToggle = () => {
    setIsGradingExpanded(!isGradingExpanded);
  };

  return (
    <div className="
      w-64 lg:w-[320px] h-full bg-primary-bg font-inter
      flex flex-col border-r border-[#0D274D] flex-none
    ">
      <div className="flex flex-col p-4 gap-5 h-full flex-1">
        <div className="flex flex-col">
          <div 
            className="cursor-pointer flex items-center p-2 gap-2 w-full min-h-[36px] hover:bg-[#0D274D] rounded transition-colors"
            onClick={handleGradingToggle}
          >
            <span className="text-white text-sm font-normal leading-5 tracking-wide flex-1">
              Conversation: Coffee Grading
            </span>
            <svg 
              className={`w-4 h-4 text-white transform transition-transform ${isGradingExpanded ? 'rotate-90' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>

          {isGradingExpanded && (
            <div className="bg-[#0D274D] rounded mt-1">
              <div 
                className={`
                  cursor-pointer flex items-center p-2 pl-6 gap-2 w-full min-h-[36px] 
                  hover:bg-[#1a3a5c] rounded transition-colors
                  ${selectedView === 'agent-to-agent' ? 'bg-[#0D274D]' : ''}
                `}
                onClick={() => onViewChange('agent-to-agent')}
              >
                <span className="text-white text-sm font-normal leading-5 tracking-wide flex-1">
                  Agent to Agent
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
