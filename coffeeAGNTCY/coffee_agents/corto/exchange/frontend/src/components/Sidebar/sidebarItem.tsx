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
      className={`cursor-pointer flex items-center w-80 h-9 gap-2 opacity-100 py-2 pr-5 pb-2 pl-12 font-inter font-normal text-sm leading-5 tracking-normal text-white ${isSelected ? 'bg-[#0D274D]' : 'bg-transparent'} ${className}`}
      onClick={onClick}
    >
      {title}
    </div>
  );
};

export default SidebarItem;
