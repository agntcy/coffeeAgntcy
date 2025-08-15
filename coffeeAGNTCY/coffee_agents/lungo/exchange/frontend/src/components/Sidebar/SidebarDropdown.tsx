/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';
import { ChevronUp } from 'lucide-react';

interface SidebarDropdownProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  isNested?: boolean;
}

const SidebarDropdown: React.FC<SidebarDropdownProps> = ({ 
  title, 
  isExpanded, 
  onToggle, 
  children,
  isNested = false
}) => {
  return (
    <div className="flex flex-col items-start p-0" style={{ width: '288px', height: '144px' }}>
            <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={onToggle}
        style={{
          width: '288px',
          height: '36px',
          gap: '8px',
          paddingTop: '8px',
          paddingRight: '20px',
          paddingBottom: '8px',
          paddingLeft: isNested ? '32px' : '20px'
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
          {title}
        </span>
        <ChevronUp 
          className={`transition-transform ${
            isExpanded ? 'rotate-0' : 'rotate-180'
          }`}
          style={{
            width: '20px',
            height: '20px',
            opacity: 1,
            color: '#E8E9EA',
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

export default SidebarDropdown;
