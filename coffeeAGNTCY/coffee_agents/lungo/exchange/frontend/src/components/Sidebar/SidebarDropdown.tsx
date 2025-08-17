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
        className={`flex items-center justify-between cursor-pointer gap-2 py-2 pr-5 ${isNested ? 'pl-8' : 'pl-5'}`}
        onClick={onToggle}
        style={{
          width: '288px',
          height: '36px'
        }}
      >
        <span 
          className="opacity-100 font-inter font-normal text-sm leading-5 tracking-wide text-white"
          style={{
            width: '208px',
            height: '20px'
          }}
        >
          {title}
        </span>
        <ChevronUp 
          className={`transition-transform w-5 h-5 opacity-100 text-[#E8E9EA] flex-none order-2 grow-0 ${
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
