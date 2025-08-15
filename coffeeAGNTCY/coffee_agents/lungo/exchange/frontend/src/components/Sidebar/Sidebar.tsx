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
  const [isGraderExpanded, setIsGraderExpanded] = useState(true); // Auto-expanded
  const [isBuyerExpanded, setIsBuyerExpanded] = useState(true); // Auto-expanded
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
      <div 
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          padding: '0px 16px',
          gap: '20px',
          width: '320px',
          height: '100%',
          background: '#23282E',
          flex: 1
        }}
      >
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
            className="flex flex-row items-start cursor-pointer"
            onClick={handleGraderToggle}
            style={{
              width: '288px',
              height: '36px',
              padding: '8px',
              gap: '8px',
              flex: 'none',
              order: 0,
              alignSelf: 'stretch',
              flexGrow: 0
            }}
          >
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
            <ChevronUp 
              className={`transition-transform ${
                isGraderExpanded ? 'rotate-0' : 'rotate-180'
              }`}
              style={{
                display: 'none',
                width: '14.375px',
                height: '8.125px',
                opacity: 1,
                position: 'relative',
                top: '6.56px',
                left: '2.81px',
                color: '#E8E9EA',
                flex: 'none',
                order: 2,
                flexGrow: 0
              }}
            />
          </div>
          
          {isGraderExpanded && (
            <div 
              className="flex flex-col items-start"
              style={{
                width: '288px',
                height: '36px',
                padding: '0px',
                background: '#0D274D',
                flex: 'none',
                order: 1,
                alignSelf: 'stretch',
                flexGrow: 0
              }}
            >
              <div 
                className="flex flex-row items-start cursor-pointer"
                onClick={handleAgentToAgentClick}
                style={{
                  width: '288px',
                  height: '36px',
                  padding: '8px 20px',
                  gap: '8px',
                  background: selectedPattern === PATTERNS.SLIM_A2A ? '#0D274D' : '#0D274D',
                  flex: 'none',
                  order: 0,
                  alignSelf: 'stretch',
                  flexGrow: 0
                }}
              >
                <span style={{
                  width: '248px',
                  height: '20px',
                  fontFamily: 'Inter',
                  fontStyle: 'normal',
                  fontWeight: 400,
                  fontSize: '14px',
                  lineHeight: '20px',
                  color: '#FFFFFF',
                  flex: 'none',
                  order: 1,
                  flexGrow: 1
                }}>
                  Agent to Agent
                </span>
              </div>
            </div>
          )}
        </div>

        <div 
          className="flex flex-col items-start font-inter"
          style={{
            padding: '0px',
            width: '288px',
            height: '524px',
            flex: 'none',
            order: 1,
            alignSelf: 'stretch',
            flexGrow: 0
          }}
        >
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
            className="flex flex-row items-start cursor-pointer"
            onClick={handleBuyerToggle}
            style={{
              width: '288px',
              height: '36px',
              padding: '8px 0px',
              gap: '8px',
              background: '#23282E',
              flex: 'none',
              order: 0,
              alignSelf: 'stretch',
              flexGrow: 0
            }}
          >
            <span style={{
              width: '288px',
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
              Conversation: Coffee Buying
            </span>
            <ChevronUp 
              className={`transition-transform ${
                isBuyerExpanded ? 'rotate-0' : 'rotate-180'
              }`}
              style={{
                display: 'none',
                width: '20px',
                height: '20px',
                flex: 'none',
                order: 2,
                flexGrow: 0
              }}
            />
          </div>
          
          {isBuyerExpanded && (
            <div 
              className="flex flex-col items-start"
              style={{
                width: '288px',
                height: '452px',
                padding: '0px',
                gap: '8px',
                flex: 'none',
                order: 1,
                alignSelf: 'stretch',
                flexGrow: 0
              }}
            >
              <div 
                className="flex flex-col items-start"
                style={{
                  padding: '0px',
                  width: '288px',
                  height: '144px',
                  flex: 'none',
                  order: 0,
                  alignSelf: 'stretch',
                  flexGrow: 0
                }}
              >
                <div 
                  className="flex items-center"
                  style={{
                    width: '288px',
                    height: '36px',
                    gap: '8px',
                    paddingTop: '8px',
                    paddingRight: '20px',
                    paddingBottom: '8px',
                    paddingLeft: '20px'
                  }}
                >
                  <span style={{
                    width: '208px',
                    height: '20px',
                    opacity: 1,
                    fontFamily: 'Inter',
                    fontWeight: 400,
                    fontSize: '14px',
                    lineHeight: '20px',
                    letterSpacing: '0.25px',
                    color: '#FFFFFF'
                  }}>
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
