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
    <div 
      className="w-[320px] h-full bg-primary-bg font-inter"
      style={{
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        padding: '16px 0px',
        width: '320px',
        height: '100%',
        borderRight: '1px solid #0D274D',
        flex: 'none',
        order: 0,
        alignSelf: 'stretch',
        flexGrow: 0
      }}
    >
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        padding: '0px 16px',
        gap: '20px',
        width: '320px',
        height: '100%',
        background: '#23282E',
        flex: 1
      }}>
     
        <div 
          className="flex flex-col items-start font-inter"
          style={{
            padding: '0px',
            width: '288px',
            height: '72px',
            flex: 'none',
            order: 0,
            alignSelf: 'stretch',
            flexGrow: 0
          }}
        >
     
        <div 
          className="cursor-pointer"
          onClick={handleGradingToggle}
          style={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'flex-start',
            padding: '8px',
            gap: '8px',
            width: '288px',
            height: '36px',
            flex: 'none',
            order: 0,
            alignSelf: 'stretch',
            flexGrow: 0
          }}
        >
          {/* (Placeholder) */}
          <div style={{
            display: 'none',
            width: '20px',
            height: '20px',
            flex: 'none',
            order: 0,
            flexGrow: 0
          }} />
          
          {/* List item */}
          <span style={{
            width: '272px',
            height: '20px',
            fontFamily: 'Inter',
            fontStyle: 'normal',
            fontWeight: 400,
            fontSize: '14px',
            lineHeight: '20px',
            letterSpacing: '0.25px',
            color: '#FFFFFF',
            flex: 'none',
            order: 1,
            flexGrow: 1
          }}>
            Conversation: Coffee Grading
          </span>
          
          <div style={{
            display: 'none',
            width: '20px',
            height: '20px',
            flex: 'none',
            order: 2,
            flexGrow: 0
          }} />
        </div>

        {isGradingExpanded && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
            padding: '0px',
            width: '288px',
            height: '36px',
            background: '#0D274D',
            flex: 'none',
            order: 1,
            alignSelf: 'stretch',
            flexGrow: 0
          }}>
            <div 
              className="cursor-pointer"
              onClick={() => onViewChange('agent-to-agent')}
              style={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'flex-start',
                padding: '8px 20px',
                gap: '8px',
                width: '288px',
                height: '36px',
                background: selectedView === 'agent-to-agent' ? '#0D274D' : 'transparent',
                flex: 'none',
                order: 0,
                alignSelf: 'stretch',
                flexGrow: 0
              }}
            >
              <div style={{
                display: 'none',
                width: '20px',
                height: '20px',
                flex: 'none',
                order: 0,
                flexGrow: 0
              }} />
              
              <span style={{
                width: '248px',
                height: '20px',
                fontFamily: 'Inter',
                fontStyle: 'normal',
                fontWeight: 400,
                fontSize: '14px',
                lineHeight: '20px',
                letterSpacing: '0.25px',
                color: '#FFFFFF',
                flex: 'none',
                order: 1,
                flexGrow: 1
              }}>
                Agent to Agent
              </span>
              
              <div style={{
                display: 'none',
                width: '20px',
                height: '20px',
                flex: 'none',
                order: 2,
                flexGrow: 0
              }} />
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
