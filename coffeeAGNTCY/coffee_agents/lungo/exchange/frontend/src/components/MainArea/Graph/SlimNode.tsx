/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { DefaultHandleColor } from "./CustomNode";

interface TransportNodeData {
    label: string;
    active?: boolean;
    handleColor?: string;
}

interface TransportNodeProps {
    data: TransportNodeData;
}

const TransportNode: React.FC<TransportNodeProps> = ({ data }) => {
 
    const activeClasses = data.active ? "bg-[#00142B] outline outline-2 outline-[#187ADC] shadow-[rgba(0,0,0,0.6)_0px_6px_8px]" : "bg-[#373C42]";
    
    return (
        <div 
            className={`
                ${activeClasses}
                text-gray-50 
                text-center
                flex items-center justify-center
                w-[1200px] h-[52px] p-4 rounded-lg
                hover:bg-[#4A4F55] hover:outline hover:outline-2 hover:outline-[#187ADC] hover:shadow-[rgba(0,0,0,0.6)_0px_6px_8px]
            `}
        >
            <div className="w-[94px] h-5 font-inter font-normal text-sm leading-5 tracking-normal text-[#E8E9EA] opacity-100 flex items-center justify-center whitespace-nowrap">
                {data.label}
            </div>
            <Handle
                type="target"
                id="top"
                position={Position.Top}
                className="w-[0.1px] h-[0.1px] border border-gray-600"
                style={{ 
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_left"
                className="w-[0.1px] h-[0.1px] border border-gray-600"
                style={{ 
                    left: '25%', 
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_center"
                className="w-[0.1px] h-[0.1px] border border-gray-600"
                style={{ 
                    left: '50%', 
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_right"
                className="w-[0.1px] h-[0.1px] border border-gray-600"
                style={{ 
                    left: '75%', 
                    background: data.handleColor || DefaultHandleColor 
                }}
            />
        </div>
    );
};

export default TransportNode;
