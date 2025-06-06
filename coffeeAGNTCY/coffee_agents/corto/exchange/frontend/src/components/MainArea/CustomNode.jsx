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

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import './styles/CustomNode.css';

export const DefaultHandleColor = '#f5f5f5'

const CustomNode = ({ data }) => {
    const nodeClass = `node ${data.active ? 'node-active' : ''}`;

    return (
        <div className={nodeClass}>
            <div className="node-icon">
                {data.icon}
            </div>
            <div className="node-content">
                <div className="node-label1">{data.label1}</div>
                <div className="node-label2">{data.label2}</div>
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