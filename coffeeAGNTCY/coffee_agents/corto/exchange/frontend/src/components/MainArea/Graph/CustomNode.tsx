/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import githubIcon from '@/assets/Github.png';
import agentDirectoryIcon from '@/assets/Agent_directory.png';

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
            className={`p-4 rounded-lg relative flex flex-col justify-start items-start gap-2 w-[193px] h-[91px] flex-none order-0 grow-0 ${activeClasses} hover:bg-[#4A4F55] hover:outline hover:outline-2 hover:outline-[#187ADC] hover:shadow-[rgba(0,0,0,0.6)_0px_6px_8px]`}
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
            </div>

            <div 
                className="h-4 font-inter font-light text-xs leading-4 text-[#E8E9EA] flex-none order-1 self-stretch flex-grow-0 whitespace-nowrap overflow-hidden text-ellipsis"
                style={{
                    width: '162px'
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
                        style={{
                            textDecoration: 'none'
                        }}
                    >
                        <div 
                            className="w-7 h-7 bg-[#00142B] rounded-lg p-1 flex justify-center items-center shadow-sm cursor-pointer opacity-100 transition-opacity duration-200 ease-in-out"
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
                    className="w-7 h-7 bg-[#00142B] rounded-lg p-1 flex justify-center items-center shadow-sm cursor-pointer opacity-100"
                >
                    <img 
                        src={agentDirectoryIcon} 
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
                    className="w-[0.1px] h-[0.1px] border border-gray-600"
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
                    className="w-[0.1px] h-[0.1px] border border-gray-600"
                    style={{
                        background: data.handleColor || DefaultHandleColor,
                    }}
                />
            )}
        </div>
    );
};

export default CustomNode;
