/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import githubIcon from '@/assets/github.svg';

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
    
    let nodeHeight = '88px'; 
    if (data.githubLink) {
        nodeHeight = '116px'; 
    }
    
    return (
        <div 
            className={`
                ${activeClasses}
                text-gray-50 
                rounded-lg 
                border 
                border-gray-100
                text-center
                flex flex-col items-center justify-center
                hover:bg-[#4A4F55] hover:outline hover:outline-2 hover:outline-[#187ADC] hover:shadow-[rgba(0,0,0,0.6)_0px_6px_8px]
                relative
            `}
            style={{ 
                width: '229px', 
                height: nodeHeight, 
                padding: '12px', 
                borderRadius: '8px',
                gap: '6px',
                opacity: 1
            }}
        >
            <div className="flex flex-row items-center p-0 gap-1 w-[197px] h-9">
                <div 
                    className="flex flex-row justify-center items-center border-none mr-0 overflow-hidden"
                    style={{
                        width: '40px',
                        height: '40px',
                        gap: '10px',
                        opacity: 1,
                        paddingTop: '4px',
                        paddingBottom: '4px',
                        borderRadius: '4px',
                        background: '#59616B'
                    }}
                >
                    {data.icon}
                </div>
                <div className="flex flex-col items-start p-0 gap-[2px] w-[173px] h-9">
                    <div className="w-[173px] h-[17px] flex items-center justify-between">
                        <span className="text-[#E8E9EA] text-left" style={{
                            fontFamily: 'Inter',
                            fontWeight: 400,
                            fontSize: '14px',
                            lineHeight: '20px',
                            letterSpacing: '0%',
                            opacity: 1
                        }}>
                            {data.label1}
                        </span>
                        {data.verificationStatus && (
                            <div 
                                style={{
                                    width: '80px',
                                    height: '20px',
                                    gap: '10px',
                                    opacity: 1,
                                    borderRadius: '20px',
                                    padding: '4px',
                                    background: data.verificationStatus === 'verified' ? '#00B98D66' : '#C6295366',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}
                            >
                                <span 
                                    style={{
                                        fontFamily: 'Inter',
                                        fontWeight: 500,
                                        fontSize: '11px',
                                        lineHeight: '16px',
                                        letterSpacing: '0%',
                                        color: '#FBFCFE'
                                    }}
                                >
                                    {data.verificationStatus === 'verified' ? 'Validated' : 'Not Validated'}
                                </span>
                            </div>
                        )}
                    </div>
                    <div className="w-[173px] h-[19px] text-[#E8E9EA] text-left self-stretch border-none bg-transparent rounded-none p-0" style={{
                        fontFamily: 'Inter',
                        fontWeight: 300,
                        fontSize: '12px',
                        lineHeight: '16px',
                        letterSpacing: '0%'
                    }}>
                        {data.label2}
                    </div>
                </div>
            </div>
            
            {data.githubLink && (
                <div className="mt-2 flex justify-center">
                    <a 
                        href={data.githubLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="hover:opacity-80 transition-opacity"
                        style={{
                            width: '32px', 
                            height: '28px',
                            gap: '10px',
                            opacity: 1,
                            borderRadius: '8px',
                            padding: '4px',
                            background: '#0051AF',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        <img 
                            src={githubIcon} 
                            alt="GitHub" 
                            style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '4px',
                                boxSizing: 'border-box'
                            }}
                        />
                    </a>
                </div>
            )}
            
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
