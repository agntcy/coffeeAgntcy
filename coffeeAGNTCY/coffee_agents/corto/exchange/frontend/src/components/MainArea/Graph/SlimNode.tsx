/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { DefaultHandleColor } from "./CustomNode";

interface SlimNodeData {
    label: string;
    active?: boolean;
    handleColor?: string;
}

interface SlimNodeProps {
    data: SlimNodeData;
}

const SlimNode: React.FC<SlimNodeProps> = ({ data }) => {
 
    const activeClasses = data.active ? "bg-[#00142B] outline outline-2 outline-[#187ADC] shadow-[rgba(0,0,0,0.6)_0px_6px_8px]" : "bg-[#373C42]";
    
    return (
        <div 
            className={`
                ${activeClasses}
                text-gray-50 
                border 
                border-gray-100
                text-center
                flex items-center justify-center
                hover:bg-[#4A4F55] hover:outline hover:outline-2 hover:outline-[#187ADC] hover:shadow-[rgba(0,0,0,0.6)_0px_6px_8px]
            `}
            style={{ 
                width: '1200px', 
                height: '52px', 
                padding: '16px', 
                borderRadius: '8px' 
            }}
        >
            <div>{data.label}</div>
            <Handle
                type="target"
                id="top"
                position={Position.Top}
                style={{ 
                    width: '0.1px', 
                    height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_left"
                style={{ 
                    left: '25%', 
                    width: '0.1px', 
                    height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_center"
                style={{ 
                    left: '50%', 
                    width: '0.1px', 
                    height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_right"
                style={{ 
                    left: '75%', 
                    width: '0.1px', 
                    height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
        </div>
    );
};

export default SlimNode;
