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
import { Handle, Position } from '@xyflow/react';

const CustomNode = ({ data, backgroundColor = '#F5F5F5', borderColor = '#A9A9A9' }) => {
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                border: `0.1px solid ${borderColor}`,
                borderLeft: '5px solid #187ADC',
                backgroundColor: `${data.backgroundColor}`,
                color: '#000000',
                borderRadius: '1em',
                width: 200,
                height: 60,
                fontFamily: "'CiscoSansTT', sans-serif",
                fontSize: '14px',
                padding: '2px 5px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                transform: 'scale(0.775)',
                transformOrigin: 'top left',
            }}
        >
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 35,
                    height: 35,
                    borderRadius: '50%',
                    backgroundColor: '#FFFFFF',
                    border: `1px solid ${borderColor}`,
                    marginRight: 10,
                }}
            >
                {data.icon}
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '3px' }}>
                <div style={{ textAlign: 'left', fontWeight: 'normal', fontSize: '12px', color: '#808080' }}>
                    {data.label1}
                </div>
                <div
                    style={{
                        textAlign: 'left',
                        fontSize: '12.5px',
                        color: 'black',
                        border: '1px #7A9EBF',
                        backgroundColor: '#EAF2FA',
                        borderRadius: '8px',
                        padding: '2.5px 5px',
                    }}
                >
                    {data.label2}
                </div>
            </div>
            {(data.handles === 'all' || data.handles === 'target') && (
                <Handle
                    type="target"
                    position={Position.Top}
                    id="target"
                    style={{ width: '0.1px', height: '0.1px', background: '#187ADC' }}
                />
            )}
            {(data.handles === 'all' || data.handles === 'source') && (
                <Handle
                    type="source"
                    position={Position.Bottom}
                    id="source"
                    style={{ width: '0.1px', height: '0.1px', background: '#187ADC' }}
                />
            )}
        </div>
    );
};

export default CustomNode;