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
import { EdgeLabelRenderer } from '@xyflow/react';
import { css } from '@emotion/react';
import './styles/CustomEdgeLabel.css';
import A2AEdgeLabel from './A2AEdgeLabel';

const CustomEdgeLabel = ({ x, y, label, icon }) => {
    if (label?.toLowerCase() === 'a2a') {
        return <A2AEdgeLabel x={x} y={y} icon={icon} />;
    }

    const dynamicStyle = css`
        position: absolute;
        left: ${x}px;
        top: ${y}px;
    `;

    return (
        <EdgeLabelRenderer>
            <div className={`custom-edge-label`} css={dynamicStyle}>
                <div className="custom-edge-label-icon">{icon}</div>
                <div className="custom-edge-label-text">{label}</div>
            </div>
        </EdgeLabelRenderer>
    );
};

export default CustomEdgeLabel;