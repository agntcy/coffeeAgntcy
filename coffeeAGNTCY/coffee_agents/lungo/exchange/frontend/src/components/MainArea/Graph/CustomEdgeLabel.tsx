/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { EdgeLabelRenderer } from '@xyflow/react';
import { css } from '@emotion/react';

interface CustomEdgeLabelProps {
    x: number;
    y: number;
    label?: string;
    active?: boolean;
}

const CustomEdgeLabel: React.FC<CustomEdgeLabelProps> = ({ x, y, label, active }) => {
    const isSlimLabel = label?.includes('SLIM');
    const isValidateLabel = label?.toLowerCase().includes('validate');
    const isLongLabel = isSlimLabel ||  isValidateLabel;
    
    const backgroundColor = active ? '#00142B' : '#183056';
    const textColor = active ? '#187ADC' : '#E8E9EA';
    
    const labelContainerStyle = css`
        position: absolute;
        transform: translate(-50%, -50%);
        left: ${x}px;
        top: ${y}px;
        pointer-events: none;
    `;

    return (
        <EdgeLabelRenderer>
            <div 
                className={`${isLongLabel ? 'w-[100px] gap-[6px]' : 'w-[34px] gap-1'} h-5 py-[2px] px-[5px] rounded-lg font-[Inter] font-normal text-xs leading-4 flex items-center justify-center opacity-100 border-none shadow-none`}
                css={labelContainerStyle}
                style={{ backgroundColor, color: textColor }}
            >
                {label && (
                    <div className="flex items-center justify-center flex-shrink-0 whitespace-nowrap font-[Inter] font-normal text-xs leading-4"
                         style={{ color: textColor }}>
                        {label}
                    </div>
                )}
            </div>
        </EdgeLabelRenderer>
    );
};

export default CustomEdgeLabel;
