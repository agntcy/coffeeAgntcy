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

const SlimNode = ({ data, backgroundColor = 'rgba(24, 122, 220, 0.4)' }) => {
    return (
        <div
            style={{
                border: '1px solid #187ADC',
                backgroundColor: backgroundColor, // Dynamic background color
                color: '#000000',
                borderRadius: 5,
                width: 625,
                height: 22,
                textAlign: 'center',
                fontFamily: "'CiscoSansTT', sans-serif",
                fontSize: '15px',

            }}
        >
            <div>{data.label}</div>
            <Handle
                type="target"
                id="top"
                position={Position.Top}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="a"
                style={{  left: '18%' }} // Offset to the left
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="b"
                style={{ left: '50%' }} // Centered
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="c"
                style={{ left: '82%' }} // Offset to the right
            />
        </div>
    );
};

export default SlimNode;
