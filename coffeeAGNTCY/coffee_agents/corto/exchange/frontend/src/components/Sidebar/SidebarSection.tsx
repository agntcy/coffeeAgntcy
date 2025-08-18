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
        className="flex flex-row items-start cursor-pointer font-inter bg-primary-bg w-72 h-9 py-2 px-0 gap-2 flex-none order-0 self-stretch grow-0"
        onClick={onToggle}
      >
        <div className="hidden w-5 h-5 flex-none order-0 grow-0" />
        
        <span className="w-72 h-5 font-inter font-normal text-sm leading-5 tracking-normal text-white flex-none order-1 grow">
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
