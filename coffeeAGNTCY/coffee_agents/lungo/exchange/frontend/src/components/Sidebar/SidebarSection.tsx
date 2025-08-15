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
  backgroundColor?: string;
}

const SidebarSection: React.FC<SidebarSectionProps> = ({ 
  title, 
  isExpanded, 
  onToggle, 
  children,
  backgroundColor = 'transparent' 
}) => {
  return (
    <div className="flex flex-col items-start p-0 w-72 h-18 flex-none order-0 self-stretch grow-0">
      <div 
        className="flex items-center justify-between cursor-pointer w-72 h-9 gap-2 py-2 text-white text-sm font-normal leading-5"
        onClick={onToggle}
        style={{
          backgroundColor,
          letterSpacing: '0.25px'
        }}
      >
        <span className="pl-2">
          {title}
        </span>
        <ChevronUp 
          className={`w-4 h-4 text-white transition-transform mr-2 ${
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

export default SidebarSection;
