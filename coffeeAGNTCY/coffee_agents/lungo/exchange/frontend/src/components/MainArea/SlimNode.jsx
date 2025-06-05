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

const SlimNode = ({ data, backgroundColor = '#F5F5F5', borderColor = '#A9A9A9' }) => {
    return (
        <div
            style={{
                display: 'flex', // Enables flexbox
                alignItems: 'center', // Vertically centers content
                justifyContent: 'center', // Horizontally centers content
                border: `0.1px solid ${borderColor}`,
                backgroundColor: backgroundColor,
                borderLeft: '5px solid #187ADC',
                color: '#000000',
                borderRadius: '0.5em',
                fontWeight: '300',
                width: 650,
                height: 25,
                textAlign: 'center',
                fontFamily: "'CiscoSansTT', sans-serif",
                fontSize: '15px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            }}
        >
            <div>{data.label}</div>
            <Handle
                type="target"
                id="top"
                position={Position.Top}
                style={{ width: '0.1px', height: '0.1px', background: '#187ADC' }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_left"
                style={{ left: '18%', width: '0.1px', height: '0.1px', background: '#187ADC' }} // Offset to the left
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_center"
                style={{ left: '50%', width: '0.1px', height: '0.1px', background: '#187ADC' }} // Centered
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_right"
                style={{ left: '82%', width: '0.1px', height: '0.1px', background: '#187ADC' }} // Offset to the right
            />
        </div>
    );
};

export default SlimNode;