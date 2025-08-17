/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';
import { ChevronUp } from 'lucide-react';

interface SidebarSectionProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const SidebarSection: React.FC<SidebarSectionProps> = ({ 
  title, 
  isExpanded, 
  onToggle, 
  children
}) => {
  return (
    <div className="flex flex-col items-start p-0 w-72 h-18 flex-none order-0 self-stretch grow-0">
      <div 
        className="flex flex-row items-start cursor-pointer font-inter bg-primary-bg"
        onClick={onToggle}
        style={{
          width: '288px',
          height: '36px',
          padding: '8px 0px',
          gap: '8px',
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
          {title}
        </span>
        <ChevronUp 
          className={`w-4 h-4 text-white transition-transform ${
            isExpanded ? 'rotate-0' : 'rotate-180'
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
      
      {isExpanded && (
        <div className="flex flex-col">
          {children}
        </div>
      )}
    </div>
  );
};

export default SidebarSection;
