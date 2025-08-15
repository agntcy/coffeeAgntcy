/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';

interface SidebarItemProps {
  title: string;
  isSelected?: boolean;
  onClick?: () => void;
  className?: string;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ 
  title, 
  isSelected = false, 
  onClick, 
  className = ""
}) => {
  return (
    <div 
      className={`
        text-white text-sm font-normal leading-5 cursor-pointer w-72 h-9
        py-2 pr-2 pl-8 flex items-center
        ${isSelected ? 'bg-[#0D274D]' : 'bg-transparent'}
        ${className}
      `}
      onClick={onClick}
      style={{ letterSpacing: '0%' }}
    >
      {title}
    </div>
  );
};

export default SidebarItem;
