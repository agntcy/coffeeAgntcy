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
      className={`cursor-pointer flex items-center ${className}`}
      onClick={onClick}
      style={{ 
        width: '320px',
        height: '36px',
        gap: '8px',
        opacity: 1,
        paddingTop: '8px',
        paddingRight: '20px',
        paddingBottom: '8px',
        paddingLeft: '48px',
        background: isSelected ? '#0D274D' : 'transparent',
        fontFamily: 'Inter',
        fontStyle: 'normal',
        fontWeight: 400,
        fontSize: '14px',
        lineHeight: '20px',
        letterSpacing: '0.25px',
        color: '#FFFFFF'
      }}
    >
      {title}
    </div>
  );
};

export default SidebarItem;
