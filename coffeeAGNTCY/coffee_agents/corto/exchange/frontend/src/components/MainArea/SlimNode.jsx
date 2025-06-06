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
import { css } from '@emotion/react';
import './styles/CustomNode.css';
import {DefaultHandleColor} from "./CustomNode.jsx";

const SlimNode = ({ data }) => {
    const nodeClass = `node slim-node ${data.active ? 'node-active' : ''}`;

    return (
        <div className={nodeClass}>
            <div>{data.label}</div>
            <Handle
                type="target"
                id="top"
                position={Position.Top}
                style={{ width: '0.1px', height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_center"
                style={{ left: '50%', width: '0.1px', height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor }}
            />
        </div>
    );
};

export default SlimNode;