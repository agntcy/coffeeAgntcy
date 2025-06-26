/**
 * Copyright 2025 Cisco Systems, Inc. and its affiliates
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { getBezierPath, BaseEdge } from '@xyflow/react';
import CustomEdgeLabel from './CustomEdgeLabel';
import LabelIcon from './LabelIcon';

const CustomEdge = ({
                        id,
                        sourceX,
                        sourceY,
                        targetX,
                        targetY,
                        sourcePosition,
                        targetPosition,
                        data,
                    }) => {
    const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });

    // Default and active edge colors
    const defaultEdgeColor = data?.active ? '#187ADC' : '#B0C4DE'; // Dark blue when active, light blue/gray otherwise

    return (
        <>
            <svg style={{ position: 'absolute', top: 0, left: 0 }}>
                <defs>
                    <marker
                        id={`${id}-arrow-start`}
                        markerWidth="5"
                        markerHeight="5"
                        refX="0.5"
                        refY="2.5"
                        orient="auto"
                    >
                        <path d="M5,0 L0,2.5 L5,5 Z" fill={defaultEdgeColor} />
                    </marker>
                    <marker
                        id={`${id}-arrow-end`}
                        markerWidth="5"
                        markerHeight="5"
                        refX="4.5"
                        refY="2.5"
                        orient="auto"
                    >
                        <path d="M0,0 L5,2.5 L0,5 Z" fill={defaultEdgeColor} />
                    </marker>
                </defs>
            </svg>
            <BaseEdge
                id={id}
                path={edgePath}
                markerStart={`url(#${id}-arrow-start)`}
                markerEnd={`url(#${id}-arrow-end)`}
                style={{
                    stroke: defaultEdgeColor,
                    strokeWidth: 2,
                    cursor: 'pointer',
                }}
            />
            <CustomEdgeLabel
                x={labelX}
                y={labelY}
                label={data.label}
                icon={<LabelIcon type={data.labelIconType} altText={`${data.labelIconType} Icon`} size={22} />}
            />
        </>
    );
};

export default CustomEdge;