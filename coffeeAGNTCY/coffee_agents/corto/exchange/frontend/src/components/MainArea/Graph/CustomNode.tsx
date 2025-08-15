/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import githubIcon from '@/assets/github.svg';
import agntcyDirectoryIcon from '@/assets/agent_directory.svg';


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
    const activeClasses = data.active ? "bg-[#00142B] outline outline-2 outline-[#187ADC] shadow-[rgba(0,0,0,0.6)_0px_6px_8px]" : "bg-[#373C42]";
    
    return (
        <div 
            className={`
                ${activeClasses}
                text-gray-50 
                rounded-lg 
                border 
                border-gray-100
                text-center
                flex flex-col items-center justify-start
                hover:bg-[#4A4F55] hover:outline hover:outline-2 hover:outline-[#187ADC] hover:shadow-[rgba(0,0,0,0.6)_0px_6px_8px]
                relative
            `}
            style={{ 
                width: '196px', 
                height: data.githubLink ? '108px' : '72px', 
                padding: '16px', 
                borderRadius: '8px' 
            }}
        >
            {data.verificationBadge && (
                <div 
                    className="absolute top-1 right-1"
                    style={{ zIndex: 10 }}
                >
                    {data.verificationBadge}
                </div>
            )}
            <div className="flex flex-row items-center p-0 gap-1 w-[148px] h-9">
                <div className="flex flex-row justify-center items-center py-1 px-0 gap-[10px] w-9 h-9 bg-[#59616B] rounded border-none mr-0 overflow-hidden opacity-100 self-stretch">
                    {data.icon}
                </div>
                <div className="flex flex-col items-start p-0 gap-[2px] w-[108px] h-9">
                    <div className="w-[108px] h-[17px] font-inter font-light text-[13px] leading-[17px] text-[#E8E9EA] text-left self-stretch">
                        {data.label1}
                    </div>
                    <div className="w-[108px] h-[19px] font-inter font-normal text-[15px] leading-[19px] text-[#E8E9EA] text-left self-stretch border-none bg-transparent rounded-none p-0">
                        {data.label2}
                    </div>
                </div>
            </div>
    <div className="absolute -right-4 top-1/2 transform -translate-y-1/2 flex flex-col gap-1">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center shadow-sm">
                    <img 
                        src={agntcyDirectoryIcon} 
                        alt="AGNTCY Directory" 
                        className="w-5 h-5 text-white" 
                    />
                </div>
                
                {data.githubLink && (
                    <a 
                        href={data.githubLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="hover:opacity-80 transition-opacity"
                    >
                        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center shadow-sm">
                            <img 
                                src={githubIcon} 
                                alt="GitHub" 
                                className="w-5 h-5 text-white"
                            />
                        </div>
                    </a>
                )}
            </div>
            {(data.handles === 'all' || data.handles === 'target') && (
                <Handle
                    type="target"
                    position={Position.Top}
                    id="target"
                    style={{
                        width: '0.1px',
                        height: '0.1px',
                        background: data.handleColor || DefaultHandleColor,
                        border: `1px solid darkgrey`,
                    }}
                />
            )}
            {(data.handles === 'all' || data.handles === 'source') && (
                <Handle
                    type="source"
                    position={Position.Bottom}
                    id="source"
                    style={{
                        width: '0.1px',
                        height: '0.1px',
                        background: data.handleColor || DefaultHandleColor,
                        border: `1px solid darkgrey`,
                    }}
                />
            )}
        </div>
    );
};

export default CustomNode;
