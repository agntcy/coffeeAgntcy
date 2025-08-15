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
}

const SidebarDropdown: React.FC<SidebarDropdownProps> = ({ 
  title, 
  isExpanded, 
  onToggle, 
  children 
}) => {
  return (
    <div className="flex flex-col items-start p-0" style={{ width: '288px', height: '144px' }}>
      <div 
        className="flex items-center justify-between cursor-pointer text-white text-sm font-normal leading-5"
        onClick={onToggle}
        style={{
          width: '288px',
          height: '36px',
          gap: '8px',
          paddingTop: '8px',
          paddingRight: '20px',
          paddingBottom: '8px',
          paddingLeft: '20px',
          letterSpacing: '0%'
        }}
      >
        <span>{title}</span>
        <ChevronUp 
          className={`w-4 h-4 text-white transition-transform ${
            isExpanded ? 'rotate-0' : 'rotate-180'
          }`}
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
