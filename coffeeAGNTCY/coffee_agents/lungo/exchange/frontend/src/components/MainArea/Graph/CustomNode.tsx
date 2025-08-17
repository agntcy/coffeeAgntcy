/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import githubIcon from '@/assets/Github.png';
import agntcyDirectoryIcon from '@/assets/Agent_directory.png';
import identityBadgeIcon from '@/assets/identity_badge.svg';

export const DefaultHandleColor = '#f5f5f5';

interface CustomNodeData {
    icon: React.ReactNode;
    label1: string;
    label2: string;
    active?: boolean;
    handleColor?: string;
    handles?: 'all' | 'target' | 'source';
    verificationStatus?: 'verified' | 'failed' | 'pending';
    verificationBadge?: React.ReactNode;
    githubLink?: string;
}

interface CustomNodeProps {
    data: CustomNodeData;
}

const CustomNode: React.FC<CustomNodeProps> = ({ data }) => {
    return (
        <div 
            className="p-4 rounded-lg bg-[#373C42] relative flex flex-col justify-start items-start gap-2"
            style={{ 
                width: '194px', 
                height: '96px',
                outline: data.active ? '2px solid #187ADC' : 'none',
                boxShadow: data.active ? 'rgba(0,0,0,0.6) 0px 6px 8px' : 'none'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.background = '#4A4F55';
                e.currentTarget.style.outline = '2px solid #187ADC';
                e.currentTarget.style.boxShadow = 'rgba(0,0,0,0.6) 0px 6px 8px';
            }}
            onMouseLeave={(e) => {
                if (!data.active) {
                    e.currentTarget.style.background = '#373C42';
                    e.currentTarget.style.outline = 'none';
                    e.currentTarget.style.boxShadow = 'none';
                }
            }}
        >
            <div 
                className="w-5 h-5 bg-[#59616B] rounded flex justify-center items-center flex-shrink-0 gap-2.5 py-1 opacity-100"
            >
                <div className="w-4 h-4 flex justify-center items-center opacity-100">
                    {data.icon}
                </div>
            </div>

            <div 
                className="flex flex-row items-center p-0 gap-1 h-5 flex-none order-0 self-stretch grow-0"
                style={{
                    width: data.verificationStatus === 'verified' ? '160px' : '162px'
                }}
            >
                <span className="h-5 font-inter font-normal text-sm leading-5 tracking-normal flex items-center text-[#E8E9EA] opacity-100 flex-none order-0 grow-0 whitespace-nowrap overflow-hidden text-ellipsis">
                    {data.label1}
                </span>
                {data.verificationStatus === 'verified' && (
                    <img 
                        src={identityBadgeIcon} 
                        alt="Verified" 
                        className="w-4 h-4 flex-none order-1 grow-0"
                    />
                )}
            </div>

            <div 
                className="h-4 font-inter font-light text-xs leading-4 text-[#E8E9EA] flex-none order-1 self-stretch flex-grow-0 whitespace-nowrap overflow-hidden text-ellipsis"
                style={{
                    width: data.verificationStatus === 'verified' ? '160px' : '162px'
                }}
            >
                {data.label2}
            </div>
            
            <div 
                className="absolute -right-4 top-1/2 -translate-y-1/2 flex flex-col gap-1 z-10"
            >
                {data.githubLink && (
                    <a 
                        href={data.githubLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="no-underline"
                    >
                        <div 
                            className="w-7 h-7 bg-[#00142B] border border-[#187ADC] rounded-lg p-1 flex justify-center items-center shadow-sm cursor-pointer opacity-100 transition-opacity duration-200 ease-in-out"
                            onMouseEnter={(e) => {
                                e.currentTarget.style.opacity = '0.8';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.opacity = '1';
                            }}
                        >
                            <img 
                                src={githubIcon} 
                                alt="GitHub" 
                                className="w-5 h-5"
                            />
                        </div>
                    </a>
                )}
                
                <div 
                    className="w-7 h-7 bg-[#00142B] border border-[#187ADC] rounded-lg p-1 flex justify-center items-center shadow-sm cursor-pointer opacity-100"
                >
                    <img 
                        src={agntcyDirectoryIcon} 
                        alt="AGNTCY Directory" 
                        className="w-5 h-5"
                    />
                </div>
            </div>
            
            {(data.handles === 'all' || data.handles === 'target') && (
                <Handle
                    type="target"
                    position={Position.Top}
                    id="target"
                    className="w-px h-px border border-gray-600"
                    style={{
                        background: data.handleColor || DefaultHandleColor,
                    }}
                />
            )}
            {(data.handles === 'all' || data.handles === 'source') && (
                <Handle
                    type="source"
                    position={Position.Bottom}
                    id="source"
                    className="w-px h-px border border-gray-600"
                    style={{
                        background: data.handleColor || DefaultHandleColor,
                    }}
                />
            )}
        </div>
    );
};

export default CustomNode;
