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
import { css } from '@emotion/react';
import a2aIcon from '../../assets/a2a_icon.png';
import { EdgeLabelRenderer } from '@xyflow/react';

const A2AEdgeLabel = ({ x, y}) => {
    const dynamicStyle = css`
        position: absolute;
        left: ${x}px;
        top: ${y}px;
    `;

    return (
        <EdgeLabelRenderer>
            <div className={`custom-edge-label`} css={dynamicStyle}>
                <img
                    src={a2aIcon}
                    alt="A2A Icon"
                    style={{
                        width: '100%',
                        height: '100%',
                        opacity: 0.9, // Slightly lighter for A2A
                        borderRadius: '0.75em', // Rounded corners for A2A
                    }}
                />
            </div>
        </EdgeLabelRenderer>
    );
};

export default A2AEdgeLabel;