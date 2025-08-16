/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import githubIcon from '@/assets/Github.png';
import agentDirectoryIcon from '@/assets/Agent_directory.png';
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
            style={{ 
                width: '194px', 
                height: '96px', 
                padding: '16px',
                borderRadius: '8px',
                background: '#373C42',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
                alignItems: 'flex-start',
                gap: '8px',
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
            {/* Icon Container - Figma Frame 1 */}
            <div 
                style={{
                    width: '20px',
                    height: '20px',
                    background: '#59616B',
                    borderRadius: '4px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    flexShrink: 0,
                    gap: '10px',
                    paddingTop: '4px',
                    paddingBottom: '4px',
                    opacity: 1
                }}
            >
                <div style={{
                    width: '16px',
                    height: '16px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    opacity: 1
                }}>
                    {data.icon}
                </div>
            </div>

            <div 
                style={{
                    display: 'flex',
                    flexDirection: 'row',
                    alignItems: 'center',
                    padding: '0px',
                    gap: '4px',
                    
                    width: '162px',
                    height: '20px',
                    
                    flex: 'none',
                    order: 0,
                    alignSelf: 'stretch',
                    flexGrow: 0
                }}
            >
                <span style={{
                    width: '115px',
                    height: '20px',
                    
                    fontFamily: 'Inter',
                    fontStyle: 'normal',
                    fontWeight: 400,
                    fontSize: '14px',
                    lineHeight: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    
                    color: '#E8E9EA',
                    
                    flex: 'none',
                    order: 0,
                    flexGrow: 0,
                    
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                }}>
                    {data.label1}
                </span>
                {data.verificationStatus === 'verified' && (
                    <img 
                        src={identityBadgeIcon} 
                        alt="Verified" 
                        style={{
                            /* verify 1 */
                            width: '16px',
                            height: '16px',
                            
                            /* Inside auto layout */
                            flex: 'none',
                            order: 1,
                            flexGrow: 0
                        }}
                    />
                )}
            </div>

            <div 
                style={{
                    width: '162px',
                    height: '16px',
                    
                    fontFamily: 'Inter',
                    fontStyle: 'normal',
                    fontWeight: 300,
                    fontSize: '12px',
                    lineHeight: '16px',
                    
                    color: '#E8E9EA',
                    
                    flex: 'none',
                    order: 1,
                    alignSelf: 'stretch',
                    flexGrow: 0,
                    
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                }}
            >
                {data.label2}
            </div>
            
            <div 
                style={{
                    position: 'absolute',
                    right: '-16px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    zIndex: 10
                }}
            >
                <div 
                    style={{
                        width: '32px',
                        height: '32px',
                        background: '#1976D2',
                        borderRadius: '50%',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.2)',
                        cursor: 'pointer'
                    }}
                >
                    <img 
                        src={agentDirectoryIcon} 
                        alt="AGNTCY Directory" 
                        style={{
                            width: '20px',
                            height: '20px'
                        }}
                    />
                </div>
                
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
                            style={{
                                width: '32px',
                                height: '32px',
                                background: '#1976D2',
                                borderRadius: '50%',
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.2)',
                                cursor: 'pointer',
                                transition: 'opacity 0.2s ease'
                            }}
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
                                style={{
                                    width: '20px',
                                    height: '20px'
                                }}
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
